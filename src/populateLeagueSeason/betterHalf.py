import http.client
import json
import collections
from google.cloud import firestore
from google.cloud import secretmanager
from datetime import datetime
from colors import (teamBorderColor, teamBackgroundColor, defaultColors)
from buildIndex import (buildIndex)
from datetime import date
from datetime import time
from datetime import datetime
from datetime import timedelta


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
# todaysDate = '2023-03-04'
todaysDateTime = datetime.today().strftime('%Y-%m-%dT:%h:%m:%s')


def getGamesForDate(request):
    request_json = request.get_json()
    # get the countryCode from the request
    countryCode = request_json['countryCode']
    # get the leagueID from the request
    leagueID = request_json['leagueID']
    # get the seasonID from the request
    season = request_json['seasonID']
    # get the startDate from the request
    startDate = request_json['startDate']
    # get the endDate from the request
    endDate = request_json['endDate']
    # get the timezone from the request
    timezone = request_json['timezone']


    # create an empty array for the games
    games = []

    # loop between startDate and endDate
    indexDate = startDate
    while indexDate <= endDate:
        # get the games for the date, and append them to games
        games = games + getGamesForDate(countryCode, leagueID, season, indexDate, timezone)
        # increment the date by 1 day
        indexDate = indexDate + timedelta(days=1) 

    # return a json object with the games
    return json.dumps(games) 


def getGamesForDate(countryCode, leagueID, season, date, timezone):

    # get today's date
    todaysDate = datetime.today().strftime('%Y-%m-%d')

    # See if we have the games for that league, season, date in the database
    dateGames = db.collection("countries/" + countryCode + 
                              "/leagues/" + str(leagueID) + 
                              "/seasons/" + str(season) + 
                              "/games/" + str(date)).get() 

    # if we have the games in the database, return them unless we're querying for today
    if dateGames.exists and date != todaysDate:
        return dateGames
    else:

        # get the games for the date
        conn.request("GET", "/v3/fixtures?league=" + str(leagueID) + 
                                        "&season=" + str(season) + 
                                        "&from=" + date 
                                        "&to=" + date
                                        "&timezone" + timezone
                                        , headers=headers)

        
        res = conn.getresponse()
        data = res.read()
        # convert the response to a json object
        data = json.loads(data.decode("utf-8"))
        # get the fixtures from the response
        fixtures = data['api']['fixtures']
        # create an empty array for the games
        games = []
        # loop through the fixtures
        for fixture in fixtures:
            homeTeam = fixture["teams"]["home"]["name"]
            awayTeam = fixture["teams"]["away"]["name"]

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

        # store the games in the firebase DB
        db.collection("countries/" + countryCode + 
                              "/leagues/" + str(leagueID) + 
                              "/seasons/" + str(season) + 
                              "/games/" + str(date)).document().set(games)
        
        return games
        
            

                            



