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
        country_ref = db.collection("countries").document(country.id)
        country_dict = country_ref.get().to_dict()

        index[country.id] = {}
        index[country.id]["display"] = country_dict["display"]
        index[country.id]["leagues"] = {}

        getLeagues(country.id)


def getLeagues(countryCode):
    leagueCollection = db.collection("countries/" + countryCode + "/leagues").stream()
    for league in leagueCollection:
        print("  " + league.id)

        league_ref = db.collection("countries/" + countryCode + "/leagues").document(league.id)
        league_dict = league_ref.get().to_dict()

        index[countryCode]["leagues"][league.id] = {}
        index[countryCode]["leagues"][league.id]["display"] = league_dict["display"]
        index[countryCode]["leagues"][league.id]["seasons"] = []

        getSeasons(countryCode, league.id)
    

def getSeasons(countryCode, leagueID):
    seasonCollection = db.collection("countries/" + countryCode + "/leagues/" + leagueID + "/seasons").stream()
    for season in seasonCollection:
        print("    " + season.id)
        index[countryCode]["leagues"][leagueID]["seasons"].append(season.id)

    

def buildIndex():
    getCountries()
    db.document("index/latest").set(index)

buildIndex()