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


@functions_framework.http
def getIndex(request):

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

    # get the index from the firebase database
    index_ref = db.document("index/latest")

    # convert the index to a dictionary
    index_dict = index_ref.get().to_dict()

    # convert the dictionary to a json string
    index_json = json.dumps(index_dict)

    # return the index
    return (index_json, 200, {'Content-Type': 'application/json', "Access-Control-Allow-Origin": "*"})
