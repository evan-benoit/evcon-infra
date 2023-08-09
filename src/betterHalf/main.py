import http.client
import json
import collections
from google.cloud import firestore
from google.cloud import secretmanager
from datetime import datetime
import datetime
from datetime import date
from datetime import timedelta
import functions_framework



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

@functions_framework.http
def getGamesForRequest(request):

    # get the countryCode from the request
    countryCode = request.args.get('countryCode')
    # get the leagueID from the request
    leagueID = request.args.get('leagueID')
    # get the seasonID from the request
    season = request.args.get('seasonID')
    # get the startDate from the request, and convert it into a date object
    startDate = datetime.datetime.strptime(request.args.get('startDate'), '%Y-%m-%d').date()
    # get the endDate from the request
    endDate = datetime.datetime.strptime(request.args.get('endDate'), '%Y-%m-%d').date()
    # get the timezone from the request
    timezone = request.args.get('timezone')


    # I feel like I'm doing this wrong
    request_json = {'countryCode': countryCode,
                    'leagueID': leagueID,
                    'seasonID': season,
                    'startDate': startDate,
                    'endDate': endDate,
                    'timezone': timezone
                    }


    games = getGamesForDateRange(countryCode, leagueID, season, startDate, endDate, timezone)

    # return a flask response with the games
    return (json.dumps(games), 200, {'Content-Type': 'application/json'})




def getGamesForDateRange(countryCode, leagueID, season, startDate, endDate, timezone):

    # create an empty array for the games
    games = []

    indexDate = startDate
    while indexDate <= endDate:
        # get the games for the date, and append them to games
        games += getGamesForDate(countryCode, leagueID, season, str(indexDate), timezone)
        # increment the date by 1 day
        indexDate = indexDate + timedelta(days=1) 

    # return a json object with the games
    return games 


def getGamesForDate(countryCode, leagueID, season, date, timezone):


    # See if we have the games for that league, season, date in the database
    dateGames = db.collection("countries/" + countryCode + 
                              "/leagues/" + str(leagueID) + 
                              "/seasons/" + str(season) + 
                              "/games").document(str(date)).get() 

    # if we have the games in the database, return them unless we're querying for today
    if dateGames.exists:
        response = dateGames.to_dict()

        gamesArray = response['games']

        return gamesArray
    else:

        requestString = "/v3/fixtures?league=" + str(leagueID) + "&season=" + str(season) + "&date=" + date + "&timezone=" + timezone

        # get the games for the date
        conn.request("GET", requestString, headers=headers)

        print ("request: " + requestString)

        
        res = conn.getresponse()
        data = res.read()
        # convert the response to a json object
        data = json.loads(data.decode("utf-8"))
        # get the fixtures from the response
        response = data['response']
        # create an empty array for the games
        games = []
        # loop through the fixtures
        for fixture in response:
            homeTeam = fixture["teams"]["home"]["name"]
            awayTeam = fixture["teams"]["away"]["name"]

            print (homeTeam + " vs " + awayTeam)

            #strip the trailing W that FOOTBALL-API adds to NWSL teams.  Fuck the patriarchy!
            homeTeam = homeTeam.rstrip(' W')
            awayTeam = awayTeam.rstrip(' W')

            homeHalftimeScore = int(fixture["score"]["halftime"]["home"])
            awayHalftimeScore = int(fixture["score"]["halftime"]["away"])

            homeFinalScore = int(fixture["score"]["fulltime"]["home"])
            awayFinalScore = int(fixture["score"]["fulltime"]["away"])

            # put these variables in a dictionary
            game = {'homeTeam': homeTeam,
                    'awayTeam': awayTeam,
                    'homeHalftimeScore': homeHalftimeScore,
                    'awayHalftimeScore': awayHalftimeScore,
                    'homeFinalScore': homeFinalScore,
                    'awayFinalScore': awayFinalScore,                
            }

            games.append(game)


        data = {}
        data["games"] = games

        # cache the results in firebase, unless it's today's date (since there may still be games in progress)
        if (date != datetime.datetime.today().strftime('%Y-%m-%d')):
            print ("storing " + json.dumps(data, indent=2))

            # store the games in the firebase DB
            db.collection("countries/" + countryCode + 
                                "/leagues/" + str(leagueID) + 
                                "/seasons/" + str(season) + 
                                "/games").document(str(date)).set(data)
            
        return games
        
            



# games = getGamesForDateRange('us', 
#                              254, 
#                              2023, 
#                              datetime.datetime.strptime('2023-08-01', '%Y-%m-%d').date(), 
#                              datetime.datetime.strptime('2023-08-08', '%Y-%m-%d').date(), 
#                              'America/New_York')

# print (games)

