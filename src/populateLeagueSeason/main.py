import http.client
import json
import collections
from google.cloud import firestore
from google.cloud import secretmanager
from datetime import datetime
from colors import (teamBorderColor, teamBackgroundColor, defaultColors)

def populateLeagueSeason(request):

    countryLeagues = [
        {
            'code' : 'us',
            'display' : 'United States',
            'leagues' : [
                {
                    'id': "254",
                    'display' : 'MLS'
                },
                {
                    'id': "253",
                    'display' : 'NWSL'
                },
            ],
        },
        {
            'code' : 'uk',
            'display' : 'UK',
            'leagues' : [
                {
                    'id': "39",
                    'display' : 'Premier League'
                },
            ],
        },
        {
            'code' : 'it',
            'display' : 'Italy',
            'leagues' : [
                {
                    'id': "135",
                    'display' : 'Serie A'
                },
            ],
        },
    ]
    
    db = firestore.Client(project='evcon-app')

    secretClient = secretmanager.SecretManagerServiceClient()
    secretName = f"projects/evcon-app/secrets/football-api-key/versions/latest"
    response = secretClient.access_secret_version(name=secretName)
    footballAPIKey = response.payload.data.decode('UTF-8')


    conn = http.client.HTTPSConnection("api-football-v1.p.rapidapi.com")

    headers = {
        'X-RapidAPI-Key': footballAPIKey,
        'X-RapidAPI-Host': "api-football-v1.p.rapidapi.com"
        }

    todaysDate = datetime.today().strftime('%Y-%m-%d')

    thisYear = datetime.today().year
    lastYear = datetime.today().year - 1

    #Look at both this year and a season that started last year (e.g. if it's 2023 look at the 2022 season)
    seasons = [thisYear, lastYear]

    #[EVTODO] If a date range was not passed in, get the last date this was run
    date = '2023-03-06'

    for country in countryLeagues:

        print ("country " + country["code"])

        countryJSdata = {
            'display' : country['display']
        }

        db.collection(u'countrySeasons').document(country["code"]).set(countryJSdata)


        for league in country['leagues']:

            print ("league " + league["id"])

            leagueJSdata = {
                'display' : league['display']
            }

            db.collection("countrySeasons/" + country["code"] + "/leagues").document(league["id"]).set(leagueJSdata)

            for season in seasons:

                #[EVTODO] Query football-api for the date range
                #[EVTODO] If there is a match on this date, get the season
                conn.request("GET", "/v3/fixtures?league=" + league['id'] + "&season=" + str(season) + "&from=" + date + "&to=" + date, headers=headers)
                res = conn.getresponse()
                rawData = res.read()
                dateFixtures = json.loads(rawData.decode("utf-8"));
                
                print (dateFixtures)

                #If a game was played for this league on this day, reprocess the entire season
                if len(dateFixtures["response"]) > 0:

                    print ("season for " + league['id'] + "/" + str(season)) 


                    conn.request("GET", "/v3/fixtures?league=" + league["id"] + "&season=" + str(season) + "&from=1900-01-01&to=" + todaysDate, headers=headers)

                    res = conn.getresponse()
                    rawData = res.read()

                    # print(data.decode("utf-8"))

                    data = json.loads(rawData.decode("utf-8"));

                    teamFixtures = collections.defaultdict(list)

                    # keep track of the earliest timestamp we see.  When we're done, we're going to create an "origin-point" one day before this (otherwise it looks like some teams start with three points!)
                    earliestTimestamp = 9000000000000 # really far future, will stop working in 2255


                    # loop through fixtures, build a dict of fixtures for each team
                    for fixture in data["response"]:

                        if fixture["fixture"]["status"]["short"] == "FT":

                            homeTeam = fixture["teams"]["home"]["name"]
                            awayTeam = fixture["teams"]["away"]["name"]

                            #strip the trailing W that FOOTBALL-API adds to NWSL teams.  Fuck the patriarchy!
                            homeTeam = homeTeam.rstrip(' W')
                            awayTeam = awayTeam.rstrip(' W')

                            homeScore = int(fixture["goals"]["home"] or 0)   
                            awayScore = int(fixture["goals"]["away"] or 0)

                            timestamp = int(fixture["fixture"]["timestamp"] * 1000 or -1) #convert to timestamp miliseconds

                            if timestamp < earliestTimestamp:
                                earliestTimestamp = timestamp

                            #Calculate points earned
                            if homeScore > awayScore:
                                homePoints = 3
                                awayPoints = 0
                            elif awayScore > homeScore:
                                awayPoints = 3
                                homePoints = 0
                            else:
                                homePoints = 1
                                awayPoints = 1

                            # create two fixtures, one for home and one for away
                            homeFixture = {'timestamp': timestamp,
                                        'teamScore': homeScore,
                                        'oppScore': awayScore,
                                        'pointsEarned': homePoints,
                                        'homeTeam': homeTeam,
                                        'homeScore': homeScore,
                                        'awayTeam': awayTeam,
                                        'awayScore': awayScore,
                                        'teamId': fixture["teams"]["home"]["id"],
                                        'teamName': fixture["teams"]["home"]["name"],
                                        }
                            
                            awayFixture = {'timestamp': timestamp,
                                        'teamScore': awayScore,
                                        'oppScore': homeScore,
                                        'pointsEarned': awayPoints,
                                        'homeTeam': homeTeam,
                                        'homeScore': homeScore,
                                        'awayTeam': awayTeam,
                                        'awayScore': awayScore,
                                        'teamId': fixture["teams"]["away"]["id"],
                                        'teamName': fixture["teams"]["away"]["name"]
                                        }
                            
                            # add to the array for each team
                            teamFixtures[homeTeam].append(homeFixture)
                            teamFixtures[awayTeam].append(awayFixture)


                    earliestTimestamp = earliestTimestamp - 86400000 * 3 #set the origin point to 3 days earlier than the earliest fixture
                    maxMatchNumber = 0
                    maxCumPoints = 0

                    #Loop through each team.  Calculate cumulative points, goals, and goal differential for each fixture
                    for teamName in teamFixtures.keys(): 
                        previousCumPoints = 0
                        previousCumGoals = 0
                        previousCumDifferential = 0
                        matchNumber = 1

                        #sort the fixtures by time
                        list.sort(teamFixtures[teamName], key=lambda d: d['timestamp'])

                        #for each fixture, compute the cumulative points
                        # for fixture in teamFixtures[teamName]:
                        for fixture in teamFixtures[teamName]:
                            cumPoints = previousCumPoints + fixture["pointsEarned"]
                            fixture["cumPoints"] = cumPoints
                            previousCumPoints = cumPoints

                            if cumPoints > maxCumPoints:
                                maxCumPoints = cumPoints
                            
                            fixture["matchNumber"] = matchNumber

                            #keep track of the maximum Match Number that's been played
                            if matchNumber > maxMatchNumber:
                                maxMatchNumber = matchNumber

                            matchNumber += 1

                            fixture["cumGoals"] = previousCumGoals + fixture["teamScore"]
                            previousCumGoals = fixture["cumGoals"]

                            fixture["cumDifferential"] = previousCumDifferential + fixture["teamScore"] - fixture["oppScore"]
                            previousCumDifferential = fixture["cumDifferential"]

                            fixture["teamLogo"] = teamLogo


                    numberOfTeams = len(teamFixtures)
                    lastFullMatchNumber = maxMatchNumber;

                    #Determine the ranking for each team for each match number
                    #For each match number 
                    for matchNumber in range(maxMatchNumber):
                        
                        #make an empty array of matches for this matchNumber
                        matches = []

                        #Loop through each team key and build an array of matches for this match number
                        for teamName in sorted(teamFixtures.keys()):

                            #If this team doesn't have this match number, it means not all matches have been played for this match number yet, so break
                            if (matchNumber >= len(teamFixtures[teamName])):
                                if (matchNumber < lastFullMatchNumber):
                                    lastFullMatchNumber = matchNumber
                                continue

                            teamFixture = teamFixtures[teamName][matchNumber]
                            matches.append(teamFixture)
                            

                        #Sort that array using the cumulative points and tiebreakers
                        for rank, teamFixture in enumerate(sorted(matches, key=lambda d: (d['cumPoints'], d['cumDifferential'], d['cumGoals']), reverse=True)):
                            teamFixture["rank"] = rank + 1
                            teamFixture["reverseRank"] = -1 * numberOfTeams + rank #the worst team has reverseRank of -1, second worse -2, etc. Used to find the "bottom five teams", etc.
                            
                    

                    #format in the chartJS json
                    chartJSdata = collections.defaultdict(list)

                    for teamNumber, teamName in enumerate(sorted(teamFixtures.keys())):

                        dataPoints = []
                        dataPoints.append({"timestamp": earliestTimestamp, "matchNumber": 0, "cumPoints": 0}) #add an origin-point for all teams

                        for fixture in sorted(teamFixtures[teamName], key=lambda d: d['timestamp']):
                            dataPoints.append({"timestamp": fixture["timestamp"], 
                                            "teamName": teamName,
                                            "matchNumber": fixture["matchNumber"], 
                                            "cumPoints": fixture["cumPoints"],
                                            "cumGoals": fixture["cumGoals"],
                                            "cumDifferential": fixture["cumDifferential"],
                                            "homeTeam": fixture["homeTeam"],
                                            "homeScore": fixture["homeScore"],
                                            "awayTeam": fixture["awayTeam"],
                                            "awayScore": fixture["awayScore"],                              
                                            "rank": fixture["rank"], 
                                            "reverseRank": fixture["reverseRank"], 
                                            })
                            
                        #look up colors for this team, or default if we don't have one
                        if teamName in teamBorderColor and teamName in teamBackgroundColor:
                            borderColor = teamBorderColor[teamName]
                            backgroundColor = teamBackgroundColor[teamName]
                        else:
                            borderColor = defaultColors[teamNumber]
                            backgroundColor = defaultColors[teamNumber]


                        chartJSdata["datasets"].append({
                            "label": teamName,
                            "borderColor": borderColor,
                            "backgroundColor": backgroundColor,
                            "tension": 0.3,
                            "stepped": True,
                            "teamLogo": fixture["teamLogo"],
                            "data": dataPoints
                        })


                    chartJSdata["lastFullMatchNumber"] = lastFullMatchNumber
                    chartJSdata["numberOfTeams"] = numberOfTeams
                    chartJSdata["maxCumPoints"] = maxCumPoints


                
                    #save to firebase
                    db.collection("countrySeasons/" + country["code"] + "/leagues/" + league["id"] + "/seasons").document(str(season)).set(chartJSdata)

    print ("success")

    return 'OK'

populateLeagueSeason(None)