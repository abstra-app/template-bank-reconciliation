import abstra.workflows as aw
import os
import requests
import uuid
from pandas.tseries.offsets import BDay
from datetime import datetime, timedelta

BREX_API_KEY = os.getenv("BREX_API_KEY")

end_date = datetime.now() - timedelta(days=1)
start_date = datetime.now() - BDay(30)


def format_response(response_data):
    output = {}

    output["bank"] = "Brex Bank"
    output["data"] = []

    for expense in response_data:
        output["data"].append({
            "id": uuid.uuid4(),
            "amount": expense["amount"]["amount"],
            "currency": expense["amount"]["currency"],
            "date": expense["posted_at_date"],
            "reason": expense["description"]
        })

    return output


def get_expenses_from_brex_api():

    url = "https://platform.brexapis.com/v2/transactions/card/primary"

    headers = {
        "Authorization": f"Bearer {BREX_API_KEY}",
    }

    query_params = {
        "purchase_at_start": start_date.strftime('%Y-%m-%d %H:%M:%S')   
    }

    try:
        response = requests.get(url, headers=headers, params=query_params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error getting expenses: {e}")
        return None
    
    response_json = response.json()
    response_data = response.get("items")

    while response_json.get("next_cursor"):
        query_params["cursor"] = response_json.get("next_cursor")

        try: 
            response = requests.get(url, headers=headers, params=query_params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error getting expenses: {e}")
            return None
        
        response_json = response.json()
        response_data += response.get("items")

    return response_data


response_data = get_expenses_from_brex_api()
formatted_response = format_response(response_data)
aw.set_data("api_output", formatted_response)