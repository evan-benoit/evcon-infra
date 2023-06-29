import json
import collections
from google.cloud import firestore
from datetime import datetime

db = firestore.Client(project='evcon-app')

index = {}

def getCountries():
    countryCollection = db.collection("countries").stream()
    for country in countryCollection:
        print(country.id)
        index[country.id] = {}

        getLeagues(country.id)


def getLeagues(countryCode):
    leagueCollection = db.collection("countries/" + countryCode + "/leagues").stream()
    for league in leagueCollection:
        print("  " + league.id)
        index[countryCode][league.id] = []

        getSeasons(countryCode, league.id)
    

def getSeasons(countryCode, leagueID):
    seasonCollection = db.collection("countries/" + countryCode + "/leagues/" + leagueID + "/seasons").stream()
    for season in seasonCollection:
        print("    " + season.id)
        index[countryCode][leagueID].append(season.id)

    

def buildIndex():
    getCountries()
    db.document("index/latest").set(index)

buildIndex()