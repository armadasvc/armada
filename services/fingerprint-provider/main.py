from fastapi import FastAPI, Request
from src.forge_arkose_fingerprint import forge_arkose_fingerprint #type: ignore
import uvicorn
from db import build_fingerprint_query,fetch_random_fingerprint
from datetime import date

app = FastAPI()

@app.get('/get-fingerprint')
async def get_fingerprint(request: Request):
    data = await request.json()
    if data["collection_date_day"] and data["collection_date_month"] and data["collection_date_year"]:
        collection_date_full = date(int(data["collection_date_year"]),int(data["collection_date_month"]),int(data["collection_date_day"]))
    else:
        collection_date_full = None

    filters = {
        "antibot_vendor": data["antibot_vendor"],
        "website":data["website"],
        "collecting_date": collection_date_full
    }


    query, params = build_fingerprint_query(filters)
    fingerprint = fetch_random_fingerprint(query, params)

    # Arkose transformer
    if data["antibot_vendor"]=="arkose":
        arkose_fingerprint = forge_arkose_fingerprint(fingerprint,data["additional_data"]["desired_ua"])
        return arkose_fingerprint

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5005)