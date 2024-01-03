import http.client
import json
import collections
from google.cloud import firestore
from google.cloud import secretmanager
from datetime import datetime
from colors import (teamBorderColor, teamBackgroundColor, defaultColors, teamTags)
from buildIndex import (buildIndex)
from datetime import date
from datetime import time
from datetime import datetime, timedelta

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
# todaysDate = '2023-09-24'
todaysDateTime = datetime.today().strftime('%Y-%m-%dT:%h:%m:%s')


#store the last updated date at the root (note that a root document is required by firestore for .collections() calls to work)
rootData = {
    'lastUpdated' : todaysDateTime
}

# db.document("countries").set(rootData)

countryLeagues = [
        {
            'code' : 'us',
            'display' : '🇺🇸US',
            'leagues' : [
                {
                    'id': 253,
                    'display' : 'Major League Soccer'
                },
                {
                    'id': 254,
                    'display' : 'National Women\'s Soccer League'
                },
            ],
        },
        {
            'code' : 'uk',
            'display' : '🇬🇧UK',
            'leagues' : [
                {
                    'id': 39,
                    'display' : 'Premier League'
                },
                {
                    'id': 40,
                    'display' : 'Championship'
                },
                {
                    'id': 41,
                    'display' : 'League One'
                },
                {
                    'id': 42,
                    'display' : 'League Two'
                },                                
            ],
        },
        {
            'code' : 'it',
            'display' : '🇮🇹IT',
            'leagues' : [
                {
                    'id': 135,
                    'display' : 'Serie A'
                },
                {
                    'id': 136,
                    'display' : 'Serie B'
                },
            ],
        },
        {
            'code' : 'de',
            'display' : '🇩🇪DE',
            'leagues' : [
                {
                    'id': 78,
                    'display' : 'Budesliga'
                },
                                {
                    'id': 79,
                    'display' : '2.Budesliga'
                },
                                {
                    'id': 80,
                    'display' : '3.Liga'
                },
            ],
        },
        {
            'code' : 'fr',
            'display' : '🇫🇷FR',
            'leagues' : [
                {
                    'id': 61,
                    'display' : 'Ligue 1'
                },
                                {
                    'id': 62,
                    'display' : 'Ligue 2'
                }
            ],
        },
    ]


def populateTodaysLeagues(request, backdate = 0):
    

    thisYear = datetime.today().year
    lastYear = datetime.today().year - 1

    #take today's date and subtract backdate days
    startDate = (datetime.today() - timedelta(days=backdate)).strftime('%Y-%m-%d')

    #Look at both this year and a season that started last year (e.g. if it's 2023 look at the 2022 season)
    seasons = [thisYear, lastYear]    

    for country in countryLeagues:

        for league in country['leagues']:

            # print ("league " + str(league["id"]))

            leagueJSdata = {
                'display' : league['display']
            }

            db.collection("countries/" + country["code"] + "/leagues").document(str(league["id"])).set(leagueJSdata)

            for season in seasons:

                conn.request("GET", "/v3/fixtures?league=" + str(league['id']) + "&season=" + str(season) + "&from=" + startDate + "&to=" + todaysDate, headers=headers)
                res = conn.getresponse()
                rawData = res.read()
                dateFixtures = json.loads(rawData.decode("utf-8"));
                
                # print (dateFixtures)

                #If a game was played for this league on this day, reprocess the entire season
                if len(dateFixtures["response"]) > 0:
                    populateLeagueSeason(country["code"], country["display"], league["id"], league["display"], season )

                   
    print ("success, building index")

    buildIndex()

    print ("success, index built")

    return 'OK'



def populateLeagueSeason(countryCode, countryDisplay, leagueID, leagueDisplay, season):

    print ("populating " + countryDisplay + ":" + leagueDisplay + ":" + str(season))

    countryJSdata = {
        'display': countryDisplay
    }

    db.collection(u'countries').document(countryCode).set(countryJSdata)

    leagueJSdata = {
        'display': leagueDisplay
    }

    db.collection(u'countries/' + countryCode + "/leagues").document(str(leagueID)).set(leagueJSdata)


    conn.request("GET", "/v3/fixtures?league=" + str(leagueID) + "&season=" + str(season) + "&from=1900-01-01&to=" + todaysDate, headers=headers)

    res = conn.getresponse()
    rawData = res.read()

    # print(data.decode("utf-8"))

    data = json.loads(rawData.decode("utf-8"));

    teamFixtures = collections.defaultdict(list)

    # keep track of the earliest timestamp we see.  When we're done, we're going to create an "origin-point" one day before this (otherwise it looks like some teams start with three points!)
    earliestTimestamp = 9000000000000 # really far future, will stop working in 2255


    # loop through fixtures, build a dict of fixtures for each team
    for fixture in data["response"]:

        #only get completed games that are in the regular season
        if fixture["fixture"]["status"]["short"] == "FT" and fixture["league"]["round"].startswith("Regular"):

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

            # Everton was docked 10 points by the PL on 11/16/2023 for violating FFL rules.  Adjust their cumulative points accordingly for their game on 11/26/23
            # this is a one-off; if the PL does this regularly we'll need to find a better way to do this
            if teamName == "Everton" and fixture["timestamp"] > 1700945958000 and fixture["timestamp"] < 1701118758000:
                print ("Everton docked 10 points")
                cumPoints -= 10

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


    numberOfTeams = len(teamFixtures)
    lastFullMatchNumber = maxMatchNumber;

    #Determine the ranking for each team for each match number
    #For each match number 
    for matchNumber in range(maxMatchNumber):
        
        #make an empty array of matches for this matchNumber
        matches = []

        # maintain a list of ranks that should be skipped (e.g. if a team hasn't played a match yet, skip its rank)
        skipRanks = []

        #Loop through each team key and build an array of matches for this match number
        for teamName in sorted(teamFixtures.keys()):

            #If this team doesn't have this match number, it means not all matches have been played for this match number yet, so break
            if (matchNumber >= len(teamFixtures[teamName])):

                #append this team's latest rank to the list of ranks to skip, below
                skipRanks.append(teamFixtures[teamName][-1]["rank"])

                if (matchNumber < lastFullMatchNumber):
                    lastFullMatchNumber = matchNumber
                continue

            teamFixture = teamFixtures[teamName][matchNumber]
            matches.append(teamFixture)
            

        #Sort that array using the cumulative points and tiebreakers
        rank = 1
        for teamFixture in sorted(matches, key=lambda d: (d['cumPoints'], d['cumDifferential'], d['cumGoals']), reverse=True):
            teamFixture["rank"] = rank
            rank += 1
            
            # if this rank is in the list of ranks to skip, skip it
            if rank in skipRanks:
                rank += 1

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

        # if the team is in the tags dict, add the tags
        if teamName in teamTags:
            tags = teamTags[teamName]
        else:
            tags = []


        chartJSdata["datasets"].append({
            "label": teamName,
            "borderColor": borderColor,
            "backgroundColor": backgroundColor,
            "tags": tags,
            "tension": 0.3,
            "stepped": True,
            "data": dataPoints
        })


    chartJSdata["lastFullMatchNumber"] = lastFullMatchNumber
    chartJSdata["numberOfTeams"] = numberOfTeams
    chartJSdata["maxCumPoints"] = maxCumPoints

    #save to firebase
    db.collection("countries/" + countryCode + "/leagues/" + str(leagueID) + "/seasons").document(str(season)).set(chartJSdata)



def backPopulate():

    today = datetime.today()

    for country in countryLeagues:
        for league in country["leagues"]:
            leagueID = league["id"]

            conn.request("GET", "/v3/leagues?id=" + str(leagueID), headers=headers)

            res = conn.getresponse()
            rawData = res.read()

            # print(data.decode("utf-8"))

            data = json.loads(rawData.decode("utf-8"));

            leagues = collections.defaultdict(list)

            for season in data["response"][0]["seasons"]:

                #The API sometimes creates seasons before they start.  Ignore them.
                seasonStart = datetime.strptime(season["start"], "%Y-%m-%d")
                if (seasonStart < today):
                    populateLeagueSeason(country["code"], country["display"], league["id"], league["display"], season["year"])

    buildIndex()


# Read the command line args, run the command specified
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Populate the league season data')
    parser.add_argument('--backpopulate', action='store_true', help='Backpopulate all seasons for all leagues')
    parser.add_argument('--buildindex', action='store_true', help='Build the index')
    parser.add_argument('--populateTodaysLeagues', action='store_true', help='Populate todays leagues')
    parser.add_argument('--backdate', type=int, default=0, help='Backdate the populateTodaysLeagues command by this many days')

    args = parser.parse_args()

    if args.backpopulate:
        backPopulate()
    elif args.buildindex:
        buildIndex()
    elif args.populateTodaysLeagues:
        populateTodaysLeagues(None, args.backdate)
    else:
        print ("No command specified.  Use --backpopulate, --buildindex, pr --populate")
