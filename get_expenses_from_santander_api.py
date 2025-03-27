from abstra.tasks import send_task
import os
import requests
import uuid
from datetime import datetime, timedelta
from pandas.tseries.offsets import BDay

# Employer Identification Number of the bank (e.g.: CNPJ in Brazil)
SANTANDER_BANK_ID = os.getenv("SANTANDER_BANK_ID")

# Account number which you want to get the expenses from (on the format routing_number.account_number)
SANTANDER_ACC_NUMBER = os.getenv("SANTANDER_ACC_NUMBER")

SANTANDER_API_KEY = os.getenv("SANTANDER_API_KEY") 

end_date = datetime.now() - timedelta(days=1)
start_date = datetime.now() - BDay(30)


def format_response(response_data):
    output = {}

    output["bank"] = "Banco Santander S. A."
    output["data"] = []

    for expense in response_data:
        output["data"].append({
            "id": uuid.uuid4(),
            "amount": expense["amount"],
            "currency": "BRL",
            "date": expense["transactionDate"],
            "reason": expense["transactionName"]
        })

    return output


def get_expenses_from_santander_api():

    base_path = "https://trust-open.api.santander.com.br/bank_account_information/v1 - Ambiente de Produção"
    endpoint = base_path + f"/banks/{SANTANDER_BANK_ID}/statements/{SANTANDER_ACC_NUMBER}"

    querystring = {
        "initialDate": start_date.strftime('%Y-%m-%d'),
        "finalDate": end_date.strftime('%Y-%m-%d'),
        "_limit": "100",
        "_offset": "1"
    }

    headers = {
        "Content-Type": "application/json",
        "api-key": SANTANDER_API_KEY
    }

    try:
        response = requests.get(endpoint, headers=headers, params=querystring)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error getting expenses: {e}")
        return None

    response_total_pages = int(response.json()["_pageable"]["totalPages"])
    response_data = response.json()["_content"]

    for page in range(2, response_total_pages + 1):
        querystring["_offset"] = str(page)

        try:
            response = requests.get(endpoint, headers=headers, params=querystring)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error getting expenses: {e}")
            return
        
        response_data += response.json()["_content"]

    return response_data


response = get_expenses_from_santander_api()
formatted_response = format_response(response)
send_task({"api_output": formatted_response})