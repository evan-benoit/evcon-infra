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

headers = {
    'X-RapidAPI-Key': footballAPIKey,
    'X-RapidAPI-Host': "api-football-v1.p.rapidapi.com"
    }

@functions_framework.http
def getGamesForRequest(request):

    # https://cloud.google.com/functions/docs/writing/write-http-functions#cors
    if request.method == "OPTIONS":
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            # allow requests from trophypace.com and localhost
            "Access-Control-Allow-Origin": "https://trophypace.com, http://localhost:1234",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600",
        }

        return ("", 204, headers)


    # get the countryCode from the request
    countryCode = request.args.get('countryCode')
    # get the leagueID from the request
    leagueID = request.args.get('leagueID')
    # get the startDate from the request, and convert it into a date object
    startDate = datetime.datetime.strptime(request.args.get('startDate'), '%Y-%m-%d').date()
    # get the endDate from the request
    endDate = datetime.datetime.strptime(request.args.get('endDate'), '%Y-%m-%d').date()
    # get the timezone from the request
    timezone = request.args.get('timezone')

    print ("received request for " + countryCode + " " + str(leagueID) + " " + str(startDate) + " " + str(endDate) + " " + timezone)

    # sanitize the inputs
    if (countryCode == None or leagueID == None or startDate == None or endDate == None or timezone == None):
        return ("Invalid request", 400, {'Content-Type': 'application/json', "Access-Control-Allow-Origin": "*"})
    #if countryCode is not a two-character string, return an error
    if (not isinstance(countryCode, str) or len(countryCode) != 2):
        return ("Invalid request", 400, {'Content-Type': 'application/json', "Access-Control-Allow-Origin": "*"})
    # if leagueID is not an integer, return an error
    if (not leagueID.isdigit()):
        return ("Invalid request", 400, {'Content-Type': 'application/json', "Access-Control-Allow-Origin": "*"})
    # if startDate is not a date, return an error
    if (not isinstance(startDate, date)):
        return ("Invalid request", 400, {'Content-Type': 'application/json', "Access-Control-Allow-Origin": "*"})
    # if endDate is not a date, return an error
    if (not isinstance(endDate, date)):
        return ("Invalid request", 400, {'Content-Type': 'application/json', "Access-Control-Allow-Origin": "*"})
    # if timezone is not a string with the format word slash word, return an error
    if (not isinstance(timezone, str) or len(timezone.split('/')) != 2):
        return ("Invalid request", 400, {'Content-Type': 'application/json', "Access-Control-Allow-Origin": "*"})
    # if startDate is after endDate, return an error
    if (startDate > endDate):
        return ("Invalid request", 400, {'Content-Type': 'application/json', "Access-Control-Allow-Origin": "*"})
    # if startDate is after today, return an error
    if (startDate > datetime.datetime.today().date()):
        return ("Invalid request", 400, {'Content-Type': 'application/json', "Access-Control-Allow-Origin": "*"})
    # if endDate is after today, return an error
    if (endDate > datetime.datetime.today().date()):
        return ("Invalid request", 400, {'Content-Type': 'application/json', "Access-Control-Allow-Origin": "*"})
    
    
    

    games = getGamesForDateRange(countryCode, leagueID, startDate, endDate, timezone)

    # return a flask response with the games
    return (json.dumps(games), 200, {'Content-Type': 'application/json', "Access-Control-Allow-Origin": "*"})




def getGamesForDateRange(countryCode, leagueID, startDate, endDate, timezone, cacheBuster = False):    

    # create an empty array for the games
    games = []

    indexDate = startDate
    while indexDate <= endDate:
        # get the games for the date, and append them to games
        games += getGamesForDate(countryCode, leagueID, str(indexDate), timezone, cacheBuster)
        # increment the date by 1 day
        indexDate = indexDate + timedelta(days=1) 

    # return a json object with the games
    return games 


def getGamesForDate(countryCode, leagueID, date, timezone, cacheBuster = False):


    # See if we have the games for that league, date in the database
    dateGames = db.collection("countries/" + countryCode + 
                              "/leagues/" + str(leagueID) + 
                              "/games").document(str(date)).get() 

    # if we have the games in the database, return them unless we're querying for today and/or cacheBuster is true
    if dateGames.exists and not cacheBuster:
        print ("retrieving: " + countryCode + " " + str(leagueID) + " " + str(date))

        response = dateGames.to_dict()

        gamesArray = response['games']

        return gamesArray
    else:

        # Loop on the date's year and the previous year, since the season may span two years
        year = date.split('-')[0]
        previousYear = str(int(year) - 1)
        years = [year, previousYear]

        # create an empty array for the games
        games = []

        numberMatches = 0

        for year in years:
            conn = http.client.HTTPSConnection("api-football-v1.p.rapidapi.com")

            requestString = "/v3/fixtures?league=" + str(leagueID) + "&season=" + year + "&date=" + date + "&timezone=" + timezone
            print ("requesting: " + requestString)

            # get the games for the date
            conn.request("GET", requestString, headers=headers)


            res = conn.getresponse()
            data = res.read()
            # convert the response to a json object
            data = json.loads(data.decode("utf-8"))
            # get the fixtures from the response
            response = data['response']

            # loop through the fixtures
            for fixture in response:
                numberMatches += 1

                fixtureID = fixture["fixture"]["id"]
                homeTeam = fixture["teams"]["home"]["name"]
                awayTeam = fixture["teams"]["away"]["name"]

                print ("processing " + homeTeam + " vs " + awayTeam + " " + str(fixtureID))

                #strip the trailing W that FOOTBALL-API adds to NWSL teams.  Fuck the patriarchy!
                homeTeam = homeTeam.rstrip(' W')
                awayTeam = awayTeam.rstrip(' W')

                try:
                    homeHalftimeScore = int(fixture["score"]["halftime"]["home"])
                    awayHalftimeScore = int(fixture["score"]["halftime"]["away"])

                    homeFinalScore = int(fixture["score"]["fulltime"]["home"])
                    awayFinalScore = int(fixture["score"]["fulltime"]["away"])
                except:
                    continue;
                
                # Edge-case!  Could the game have been a near comeback?
                # Look for games where the winner was winning at half, but the loser's final score was equal or greater to the
                # winner's score at halftime.  We'll need to check to see if the loser tied up the game in the second half
                # by looking at the game goal-by-goal
                nearComeback = False
                if ((homeFinalScore > awayFinalScore 
                     and homeHalftimeScore > awayHalftimeScore 
                     and awayFinalScore >= homeHalftimeScore) 
                    or 
                    (awayFinalScore > homeFinalScore 
                     and awayHalftimeScore > homeHalftimeScore 
                     and homeFinalScore >= awayHalftimeScore)):
                    nearComeback = checkForNearComeback(fixtureID, homeTeam, awayTeam)
            


                # put these variables in a dictionary
                game = {'date' : date,
                        'fixtureID': fixtureID,
                        'homeTeam': homeTeam,
                        'awayTeam': awayTeam,
                        'homeHalftimeScore': homeHalftimeScore,
                        'awayHalftimeScore': awayHalftimeScore,
                        'homeFinalScore': homeFinalScore,
                        'awayFinalScore': awayFinalScore,  
                        'nearComback': nearComeback              
                }

                games.append(game)


        data = {}
        data["games"] = games

        # cache the results in firebase, unless it's today's date and there are matches (since there may still be games in progress)
        if not (date == datetime.datetime.today().strftime('%Y-%m-%d') and numberMatches > 0):
            # print ("storing " + json.dumps(data, indent=2))

            # store the games in the firebase DB
            db.collection("countries/" + countryCode + 
                                "/leagues/" + str(leagueID) + 
                                "/games").document(str(date)).set(data)
            
        return games
        
def checkForNearComeback(fixtureID, homeTeam, awayTeam):

    print ("checking for near comeback")   

    conn = http.client.HTTPSConnection("api-football-v1.p.rapidapi.com")

    requestString = "/v3/fixtures/events?fixture=" + str(fixtureID)

    conn.request("GET", requestString, headers=headers)

    res = conn.getresponse()
    data = res.read()
    # convert the response to a json object
    data = json.loads(data.decode("utf-8"))
    # get the fixtures from the response
    response = data['response']

    score = {"home": 0, "away": 0}

    # loop through the events in the response
    for event in response:
        if (event['type'] == 'Goal'):
            # get the name of the team that scored
            teamName = event['team']['name']
            # if it was the home team, increment the home score
            if (teamName == homeTeam):
                score['home'] += 1
            # if it was the away team, increment the away score
            elif (teamName == awayTeam):
                score['away'] += 1

            # get the elapsed time
            elapsed = event['time']['elapsed'] 

            # if it is past the 45th minute, and the game is now tied, then it is a near comeback
            if (elapsed > 45 and score['home'] == score['away']):
                return True

    # If the game was never tied in the second half, then it's not a near comeback
    return False
            



# use argparse to read the command line arguments for the country code, league ID, start date, end date, and timezone
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("countryCode", help="the country code for the league")
    parser.add_argument("leagueID", help="the league ID")
    parser.add_argument("startDate", help="the start date")
    parser.add_argument("endDate", help="the end date")
    parser.add_argument("timezone", help="the timezone")
    parser.add_argument("--cacheBuster", help="whether to ignore the cache", action="store_true", default=False)
    args = parser.parse_args()

    # parse the startDate and endDate into a date object
    args.startDate = datetime.datetime.strptime(args.startDate, '%Y-%m-%d').date()
    args.endDate = datetime.datetime.strptime(args.endDate, '%Y-%m-%d').date()

    games = getGamesForDateRange(args.countryCode, args.leagueID, args.startDate, args.endDate, args.timezone, args.cacheBuster)

    print (games)

