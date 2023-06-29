import json
import collections
from google.cloud import firestore
from datetime import datetime

db = firestore.Client(project='evcon-app')


def getCountries():
    # Code from https://firebase.google.com/docs/firestore/query-data/get-data#get_all_documents_in_a_collection but it doesn't work!
    countryCollection = db.collection("countries").stream()
    for country in countryCollection:
        print(country.id)
        #evtodo build a dict of the countries, leagues, and seasons, and store it.

def getLeagues(countryCode):
    i = 1

def getSeasons(countryCode, leagueID):
    i = 1

def buildIndex():
    data = getCountries()
    # db.document("index").set(data)

buildIndex()