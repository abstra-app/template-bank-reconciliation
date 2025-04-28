from abstra.tasks import send_task
import os
import requests
from requests.auth import HTTPBasicAuth
import uuid
from pandas.tseries.offsets import BDay
from datetime import datetime, timedelta

CERTIFICATION_PATH = os.getenv("CERTIFICATION_PATH")
CLARA_CERTIFICATION_PATH = os.getenv("CLARA_CERTIFICATION_PATH")
CLARA_API_KEY_PATH = os.getenv("CLARA_API_KEY_PATH")
CLARA_CLIENT_ID = os.getenv("CLARA_CLIENT_ID")
CLARA_CLIENT_SECRET = os.getenv("CLARA_CLIENT_SECRET")

start_date = datetime.now() - BDay(30)
end_date = datetime.now() - timedelta(days=1)


def format_response(response_data):
    output = {}

    output["bank"] = "Banco Clara S.A."
    output["data"] = []

    for expense in response_data:
        output["data"].append({
            "id": uuid.uuid4(),
            "amount": expense["amount"]["total"],
            "currency": expense["amount"]["currency"],
            "date": expense["operationDate"],
            "reason": expense["label"]
        })

    return output


def get_expenses_from_clara_api():

    # get access token
    # brazil clara token url
    token_url = "https://public-api.br.clara.com/oauth/token"
    cert = (f"{CERTIFICATION_PATH}.crt", f"{CLARA_API_KEY_PATH}.key")
    auth = HTTPBasicAuth(CLARA_CLIENT_ID, CLARA_CLIENT_SECRET)

    try:
        response_token = requests.post(
            token_url, 
            auth=auth, 
            cert=cert, 
            verify=f"{CLARA_CERTIFICATION_PATH}.pem"
        )
        response_token.raise_for_status()
        token = response_token.json().get('access_token')
    except requests.exceptions.RequestException as e:
        print(f"Error getting token: {e}")
        raise SystemExit(e)
    

    # brazil clara transaction url
    transaction_url = "https://public-api.br.clara.com/api/v2/transactions"

    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json"
    }

    query_params = {
        "operationDateRangeStart": start_date.strftime('%Y-%m-%d'),
        "operationDateRangeEnd": end_date.strftime('%Y-%m-%d'),
        "page": 0,
    }

    try:
        response_expenses = requests.get(
            transaction_url, 
            headers=headers,
            params=query_params,
            cert=cert,
            verify=f"{CLARA_CERTIFICATION_PATH}.pem"
        ) 
        response_expenses.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error getting expenses: {e}")
        raise SystemExit(e)
    
    expenses_data = response_expenses.json().get("content")
    is_last_page = response_expenses.json().get("last")

    while not is_last_page:
        query_params["page"] += 1
        try:
            response_expenses = requests.get(
                transaction_url, 
                headers=headers,
                params=query_params,
                cert=cert,
                verify=f"{CLARA_CERTIFICATION_PATH}.pem"
            )
            response_expenses.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error getting expenses: {e}")
            raise SystemExit(e)
    
        expenses_data += response_expenses.json().get("content")
        is_last_page = response_expenses.json().get("last")

    return expenses_data


response_data = get_expenses_from_clara_api()
formatted_response = format_response(response_data)
send_task({"api_output": formatted_response})