# scripts/test_ee_init.py
"""
Test Earth Engine initialization using a service account.
This version works across all ee API versions (no advanced cloud API calls).
"""

import os
import json
import sys

try:
    from google.oauth2 import service_account
    import ee
except Exception as e:
    print("IMPORT ERROR:", e)
    sys.exit(2)

KEY = os.environ.get("GEE_KEY", "key.json")
PROJECT = os.environ.get("GEE_PROJECT", "radiant-works-474616-t3")

print("Using key file:", KEY)
if not os.path.exists(KEY):
    print("ERROR: key file not found at", KEY)
    sys.exit(2)

with open(KEY, "r") as f:
    j = json.load(f)
    print("client_email:", j.get("client_email", "<missing>"))

# Create Google credentials
try:
    creds = service_account.Credentials.from_service_account_file(
        KEY,
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/earthengine"
        ]
    )
    print("Created google credentials object OK")
except Exception as e:
    print("Failed creating credentials:", type(e).__name__, e)
    sys.exit(2)

# Initialize Earth Engine
try:
    print("Initializing Earth Engine…")
    ee.Initialize(credentials=creds, project=PROJECT)
    print("EE Initialize succeeded. Running test getInfo()…")
    print("EE test result:", ee.Number(1).getInfo())
    print("All good! You can now submit EE export tasks.")
except Exception as e:
    print("EE Initialize FAILED:", type(e).__name__, e)
    import traceback
    traceback.print_exc()
    sys.exit(3)