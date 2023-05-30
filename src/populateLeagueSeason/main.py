import http.client
import json
import collections
from google.cloud import firestore
from datetime import datetime

def populateLeagueSeason(request):

    activeSeasons = [
        {
            'league' : '39', #Premier League
            'season' : '2022'
        },
        {
            'league' : '254', #NWSL
            'season' : '2023'
        },
        {
            'league' : '135', #Serie A
            'season' : '2022'
        },
        {
            'league' : '253', #Major League Soccer
            'season' : '2023'
        },        
    ] 


    teamBorderColor = {
        'Arsenal' : '#023474',
        'Aston Villa' : '#670e36',
        'Bournemouth' : '#ed1c24',
        'Brentford' : '#140e0c',
        'Brighton' : '#005daa',
        'Chelsea' : '#034694',
        'Crystal Palace' : '#292d6b',
        'Everton' : '#274488',
        'Fulham' : '#000000',
        'Leeds' : '#1d428a',
        'Leicester' : '#0053a0',
        'Liverpool' : '#dd0000',
        'Manchester City' : '#6caddf',
        'Manchester United' : '#b54005',
        'Newcastle' : '#00b6f1',
        'Nottingham Forest' : '#e53233',
        'Southampton' : '#ed1a3b',
        'Tottenham' : '#132257',
        'West Ham' : '#2dafe5',
        'Wolves' : '#231f20',
    }

    teamBackgroundColor = {
        'Arsenal' : '#db0007',
        'Aston Villa' : '#95bfe5',
        'Bournemouth' : '#000000',
        'Brentford' : '#e30613',
        'Brighton' : '#ffffff',
        'Chelsea' : '#dba111',
        'Crystal Palace' : '#000000',
        'Everton' : '#000000',
        'Fulham' : '#cc0000',
        'Leeds' : '#ffcd00',
        'Leicester' : '#fdb311',
        'Liverpool' : '#dd0000',
        'Manchester City' : '#ffc758',
        'Manchester United' : '#ffe500',
        'Newcastle' : '#bbbdbf',
        'Nottingham Forest' : '#000000',
        'Southampton' : '#000000',
        'Tottenham' : '#ffffff',
        'West Ham' : '#7c2c3b',
        'Wolves' : '#fdb913',
    }




    conn = http.client.HTTPSConnection("api-football-v1.p.rapidapi.com")

    headers = {
        'X-RapidAPI-Key': "bd4c89aaccmshb317afc95667941p1c0f98jsna8a191b4f7be",
        'X-RapidAPI-Host': "api-football-v1.p.rapidapi.com"
        }

    todaysDate = datetime.today().strftime('%Y-%m-%d')

    for activeSeason in activeSeasons:


        conn.request("GET", "/v3/fixtures?league=" + activeSeason['league'] + "&season=" + activeSeason['season'] + "&from=1900-01-01&to=" + todaysDate, headers=headers)

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
        maxMatchNumber = 0;

        #Loop through each team.  Calculate cumulative points, goals, and goal differential for each fixture
        for teamName in teamFixtures.keys(): 
            previousCumPoints = 0
            previousCumGoals = 0
            previousCumDifferential = 0
            matchNumber = 1

            #get the URL to the team logo
            # conn.request("GET", "/v3/teams/statistics?league=" + activeSeason['league'] + "&season=" + activeSeason['season'] + "&team=" + str(teamFixtures[teamName][0]["teamId"]), headers=headers)
            # res = conn.getresponse()
            # rawData = res.read()
            # data = json.loads(rawData.decode("utf-8"));

            # teamLogo = data["response"]["team"]["logo"]
            teamLogo = ""

            #sort the fixtures by time
            list.sort(teamFixtures[teamName], key=lambda d: d['timestamp'])

            #for each fixture, compute the cumulative points
            # for fixture in teamFixtures[teamName]:
            for fixture in teamFixtures[teamName]:
                fixture["cumPoints"] = previousCumPoints + fixture["pointsEarned"]
                previousCumPoints = fixture["cumPoints"]
                
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

        for teamName in sorted(teamFixtures.keys()):

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
                
                    
            if teamName in teamBorderColor and teamName in teamBackgroundColor:

                chartJSdata["datasets"].append({
                    "label": teamName,
                    "borderColor": teamBorderColor[teamName],
                    "backgroundColor": teamBackgroundColor[teamName],
                    "tension": 0.3,
                    "stepped": False,
                    "teamLogo": fixture["teamLogo"],
                    "data": dataPoints
                })

            else:
                chartJSdata["datasets"].append({
                    "label": teamName,
                    "tension": 0.3,
                    "stepped": False,
                    "teamLogo": fixture["teamLogo"],
                    "data": dataPoints,
                })

        chartJSdata["lastFullMatchNumber"] = lastFullMatchNumber

        firebaseRecordKey = activeSeason['league'] + "-" + activeSeason['season']

        #save to firebase
        db = firestore.Client(project='evcon-app')
        db.collection(u'leagueSeasons').document(firebaseRecordKey).set(chartJSdata)

    print ("success")

    return 'OK'

populateLeagueSeason(None)