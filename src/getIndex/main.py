import json
from google.cloud import firestore
import functions_framework
import os
import logging
import traceback
import sys
import google.auth
creds, project = google.auth.default()
print(f"Running as {creds.service_account_email}")

project_id = os.environ["PROJECT_ID"]

db = firestore.Client(project=project_id)

# ---------- Logging ----------
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(message)s"
)

def log_json(level, message, **kwargs):
    entry = {
        "severity": level,
        "message": message,
        **kwargs
    }
    print(json.dumps(entry))   # Cloud Logging parses JSON

# ---------- Config ----------
ALLOWED_ORIGINS = {
    "http://trophypace.com",
    "https://trophypace.com",
    "http://localhost:1234"
}

def cors_headers(origin):
    if origin in ALLOWED_ORIGINS:
        return {"Access-Control-Allow-Origin": origin}
    return {"Access-Control-Allow-Origin": "null"}

# ---------- Function ----------
@functions_framework.http
def getIndex(request):
    try:
        origin = request.headers.get("Origin", "")
        log_json("INFO", "getIndex called", method=request.method, origin=origin)

        # Handle CORS preflight
        if request.method == "OPTIONS":
            headers = {
                **cors_headers(origin),
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Max-Age": "3600",
            }
            return ("", 204, headers)

        # Fetch Firestore doc
        log_json("INFO", "fetching index doc", collection="index", doc="latest")
        index_ref = db.document("index/latest")
        index_dict = index_ref.get().to_dict() or {}
        log_json("INFO", "fetched index", size=len(index_dict))

        index_json = json.dumps(index_dict)
        return (
            index_json,
            200,
            {"Content-Type": "application/json", **cors_headers(origin)},
        )

    except Exception as e:
        tb = traceback.format_exc()
        log_json("ERROR", "Exception in getIndex", error=str(e), traceback=tb)
        return (
            json.dumps({"error": "Internal Server Error"}),
            500,
            {"Content-Type": "application/json", **cors_headers(request.headers.get("Origin", ""))},
        )