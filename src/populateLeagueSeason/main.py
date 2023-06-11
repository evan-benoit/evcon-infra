import http.client
import json
import collections
from google.cloud import firestore
from google.cloud import secretmanager
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
        #premier league
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
 
        #NWSL
        'Angel City' : "#F2D4D7",
        'Chicago Red Stars' : "#d22030",
        'Houston Dash' : "#f36018",
        'Kansas City' : "#CB333B",
        'NJ/NY Gotham FC' : "#9ADBE8",
        'North Carolina Courage' : "#ab1d37",
        'OL Reign' : "#e62929",
        'Orlando Pride' : "#00a7e1",
        'Portland Thorns' : "#971d1f",
        'Racing Louisville' : "#1E1A34",
        'San Diego Wave' : "#00C1D4",
        'Washington Spirit' : "#c31b32",


        #MLS
        'Atlanta United': '#02438f',
        'Austin FC': '#000',
        'Charlotte': '#186cb5',
        'Chicago Fire': '#0f1637',
        'Colorado Rapids': '#711827',
        'Columbus Crew': '#1a1718',
        'DC United': '#e7002c',
        'FC Cincinnati': '#011f74',
        'FC Dallas': '#af0030',
        'Houston Dynamo': '#f17311',
        'Inter Miami': '#1a1718',
        'Los Angeles Galaxy': '#01184a',
        'Los Angeles FC': '#000',
        'Minnesota United FC': '#464746',
        'Montreal Impact': '#224e9d',
        'Nashville SC': '#1a103c',
        'New England Revolution': '#db002b',
        'New York City FC': '#061533',
        'New York Red Bulls': '#032152',
        'Orlando City SC': '#4d0f8c',
        'Philadelphia Union': '#032043',
        'Portland Timbers': '#073a0f',
        'Real Salt Lake': '#a1002b',
        'San Jose Earthquakes': '#181818',
        'Seattle Sounders': '#1d4d7f',
        'Sporting Kansas City': '#011d4a',
        'St. Louis City': '#011128',
        'Toronto FC': '#990d22',
        'Vancouver Whitecaps FC': '#061a4a',
    }

    teamBackgroundColor = {

        #Premier League
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


        #NWSL
        'Angel City' : "#010101",
        'Chicago Red Stars' : "#42b7e6",
        'Houston Dash' : "#9cc2ea",
        'Kansas City' : "#091F2C",
        'NJ/NY Gotham FC' : "#010101",
        'North Carolina Courage' : "#09426a",
        'OL Reign' : "#003692",
        'Orlando Pride' : "#633394",
        'Portland Thorns' : "#ffffff",
        'Racing Louisville' : "#C5B4E3",
        'San Diego Wave' : "#041E42",
        'Washington Spirit' : "#171e27",

        #MLS
        'Atlanta United': '#8f7f4e',
        'Austin FC': '#16a631',
        'Charlotte': '#f5f5f5',
        'Chicago Fire': '#a21522',
        'Colorado Rapids': '#79a8e2',
        'Columbus Crew': '#fef209',
        'DC United': '#1a1718',
        'FC Cincinnati': '#fb3709',
        'FC Dallas': '#001548',
        'Houston Dynamo': '#7cb8e8',
        'Inter Miami': '#1a1718',
        'Los Angeles Galaxy': '#fecb07',
        'Los Angeles FC': '#b58d5b',
        'Minnesota United FC': '#8ac2dd',
        'Montreal Impact': '#2a2829',
        'Nashville SC': '#e0dc48',
        'New England Revolution': '#021e4a',
        'New York City FC': '#5b9add',
        'New York Red Bulls': '#d90040',
        'Orlando City SC': '#fedd81',
        'Philadelphia Union': '#a3750b',
        'Portland Timbers': '#e6e61f',
        'Real Salt Lake': '#05296d',
        'San Jose Earthquakes': '#243366',
        'Seattle Sounders': '#537d16',
        'Sporting Kansas City': '#82a0ce',
        'St. Louis City': '#cb0038',
        'Toronto FC': '#313733',
        'Vancouver Whitecaps FC': '#82b5de',
    }


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
        maxMatchNumber = 0
        maxCumPoints = 0

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
                    "stepped": True,
                    "teamLogo": fixture["teamLogo"],
                    "data": dataPoints
                })

            else:
                chartJSdata["datasets"].append({
                    "label": teamName,
                    "tension": 0.3,
                    "stepped": True,
                    "teamLogo": fixture["teamLogo"],
                    "data": dataPoints,
                })

        chartJSdata["lastFullMatchNumber"] = lastFullMatchNumber
        chartJSdata["numberOfTeams"] = numberOfTeams
        chartJSdata["maxCumPoints"] = maxCumPoints


        firebaseRecordKey = activeSeason['league'] + "-" + activeSeason['season']

        #save to firebase
        db = firestore.Client(project='evcon-app')
        db.collection(u'leagueSeasons').document(firebaseRecordKey).set(chartJSdata)

    print ("success")

    return 'OK'

populateLeagueSeason(None)