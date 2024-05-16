from google.cloud import secretmanager
import http.client
import json


#when it doubt, look them up at https://teamcolorcodes.com
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

    #Serie A
    'AC Milan': '#000',
    'AS Roma': '#791224',
    'Atalanta': '#195baa',
    'Bologna': '#152238',
    'Cremonese': '#b78b3e',
    'Empoli': '#094492',
    'Fiorentina': '#371b80',
    'Inter': '#90804f',
    'Juventus': '#000',
    'Lazio': '#77cff5',
    'Lecce': '#e6001c',
    'Monza': '#bb0024',
    'Napoli': '#032b6e',
    'Salernitana': '#881123',
    'Sampdoria': '#174084',
    'Sassuolo': '#149a41',
    'Spezia': '#131517',
    'Torino': '#761205',
    'Udinese': '#000',
    'Verona': '#37428a',
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

    #Serie A
    'AC Milan': '#f6000d',
    'AS Roma': '#ebb033',
    'Atalanta': '#000',
    'Bologna': '#8f0c1d',
    'Cremonese': '#b3000d',
    'Empoli': '#f2efde',
    'Fiorentina': '#90804d',
    'Inter': '#095397',
    'Juventus': '#000',
    'Lazio': '#77cff5',
    'Lecce': '#fff20c',
    'Monza': '#f5f5f5',
    'Napoli': '#178ecd',
    'Salernitana': '#f5f5f5',
    'Sampdoria': '#b20014',
    'Sassuolo': '#000',
    'Spezia': '#a1874d',
    'Torino': '#e9a211',
    'Udinese': '#786a2a',
    'Verona': '#ebd812',
}


# Grabbed these from https://lospec.com/palette-list/30-color
defaultColors = [
    '#201923',
    '#000000',
    '#fcff5d',
    '#7dfc00',
    '#0ec434',
    '#228c68',
    '#8ad8e8',
    '#235b54',
    '#29bdab',
    '#3998f5',
    '#37294f',
    '#277da7',
    '#3750db',
    '#f22020',
    '#991919',
    '#ffcba5',
    '#e68f66',
    '#c56133',
    '#96341c',
    '#632819',
    '#ffc413',
    '#f47a22',
    '#2f2aa0',
    '#b732cc',
    '#772b9d',
    '#f07cab',
    '#d30b94',
    '#edeff3',
    '#c3a5b4',
    '#946aa2',
    '#5d4c86',
]



#quick script to get a list of team names, so we can cut-and-paste into the dictionary above and then get their colors
def getBlankColorDict(leagueID, season):
    secretClient = secretmanager.SecretManagerServiceClient()
    secretName = f"projects/evcon-app/secrets/football-api-key/versions/latest"
    response = secretClient.access_secret_version(name=secretName)
    footballAPIKey = response.payload.data.decode('UTF-8')

    conn = http.client.HTTPSConnection("api-football-v1.p.rapidapi.com")

    headers = {
        'X-RapidAPI-Key': footballAPIKey,
        'X-RapidAPI-Host': "api-football-v1.p.rapidapi.com"
        }

    conn.request("GET", "/v3/teams?league=" + str(leagueID) + "&season=" + str(season), headers=headers)
    res = conn.getresponse()
    rawData = res.read()
    data = json.loads(rawData.decode("utf-8"));

    teams = []

    for team in data["response"]:
        teams.append(team["team"]["name"])
    
    for team in sorted(teams):        
        print ("'" + team + "': '',")


# getBlankColorDict(135, 2022)


teamTags = {
    #premier league
    'Arsenal' : ['London', 'North London Derby'],
    'Aston Villa' : [],
    'Bournemouth' : [],
    'Brentford' : ['London'],
    'Brighton' : [],
    'Chelsea' : ['London'],
    'Crystal Palace' : ['London'],
    'Everton' : ['Liverpool'],
    'Fulham' : ['London'],
    'Leeds' : [],
    'Leicester' : [],
    'Liverpool' : ['Liverpool'],
    'Manchester City' : ['Manchester Derby'],
    'Manchester United' : ['Manchester Derby'],
    'Newcastle' : [],
    'Nottingham Forest' : [],
    'Southampton' : [],
    'Tottenham' : ['London', 'North London Derby'],
    'West Ham' : ['London'],
    'Wolves' : [],
}


teamDockedPoints = {
    'Everton' : [
        {
            'date' : 1701118758000,
            'points' : 8
        }
    ],
    'Nottingham Forest' : [
         {
            'date' : 1710793309000,
            'points' : 4
        }
    ],       

    }         