import abstra.workflows as aw
import os
import requests
import uuid
from pandas.tseries.offsets import BDay
from datetime import datetime, timedelta

INTER_CLIENT_SECRET = os.getenv("INTER_CLIENT_SECRET")
INTER_CLIENT_ID = os.getenv("INTER_CLIENT_ID")
CERTIFICATION_PATH = os.getenv("CERTIFICATION_PATH")
INTER_API_KEY_PATH = os.getenv("INTER_API_KEY_PATH")
INTER_ACC_NUMBER = os.getenv("INTER_ACC_NUMBER")

end_date = datetime.now() - timedelta(days=1)
start_date = datetime.now() - BDay(30)


def format_response(response):
    output = {}
    response_json = response.json()

    output["bank"] = "Banco Inter S.A."
    output["data"] = []

    for expense in response_json["transacoes"]:
        output["data"].append({
            "id": uuid.uuid4(),
            "amount": expense["valor"],
            "currency": "BRL",
            "date": expense["dataEntrada"],
            "reason": expense.get("descricao") if expense.get("descricao") else expense.get("titulo")
        })

    return output


def get_expenses_from_inter_api():

    # request access token
    token_endpoint = "https://cdpj.partners.bancointer.com.br/oauth/v2/token"
    token_request_body = f"client_id={INTER_CLIENT_ID}&client_secret={INTER_CLIENT_SECRET}&scope=extrato.read&grant_type=client_credentials"
    token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    cert=(f'{CERTIFICATION_PATH}.crt', f'{INTER_API_KEY_PATH}.key')

    try:
        token_response = requests.post(
            token_endpoint,
            cert=cert,
            data=token_request_body,
            headers=token_headers
        )
        token_response.raise_for_status()
        token = token_response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error getting token: {e}")
        raise SystemExit(e)

    expenses_endpoint = "https://cdpj.partners.bancointer.com.br/banking/v2/extrato"

    filters = {
        "dataInicio": start_date.strftime('%Y-%m-%d'),
        "dataFim": end_date.strftime('%Y-%m-%d'),
    }

    expenses_headers = {
        "Authorization": "Bearer " + token,
        "x-conta-corrente": INTER_ACC_NUMBER,
        "Content-Type": "Application/json",
    }

    try:
        expenses_response = requests.get(
            expenses_endpoint,
            params=filters,
            headers=expenses_headers,
            cert=cert
        )
        expenses_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error getting expenses: {e}")
        raise SystemExit(e)

    return expenses_response


response = get_expenses_from_inter_api()
formatted_response = format_response(response)
formatted_response["data"] = formatted_response["data"][:10]
aw.set_data("api_output", formatted_response)