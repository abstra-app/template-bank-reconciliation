from abstra.tasks import send_task, get_tasks
import abstra.tables as at
import os 
from utils.abstra_ai_prompts import AIPrompts
from utils.expenses_entities import InternalTrackingExpenses

notification_email = os.getenv("FINANCE_TEAM_EMAIL")

# get the latest task from the API
tasks = get_tasks()
task = tasks[0]
payload = task.payload
api_output = payload["api_output"]
api_output_data = api_output["data"]
expenses_bank = api_output["bank"]


table_rows = at.select("internal_tracking_expenses", where={"verified": False, "bank": expenses_bank})
database_expenses = [InternalTrackingExpenses(row) for row in table_rows]

unmatched_expenses = []

# check if the expenses from the API match the expenses in the database based on amount, date, currency, and reason
# additionaly, uses AI to check the reason if the reason is not an exact match
for api_expense in api_output_data:
    match_found = False 
    for intern_expense in database_expenses:
        if (api_expense["amount"] * 100 == intern_expense.amount * 100 and
            api_expense["date"] == intern_expense.date and
            api_expense["currency"] == intern_expense.currency and
            (AIPrompts.reason_ai_check(api_expense["reason"], intern_expense.reason)) or (api_expense["reason"] == intern_expense.reason)
        ):
            match_found = True
            at.update("internal_tracking_expenses", where={"id": intern_expense.id}, set={"verified": "true"})
            break
    if not match_found:
        unmatched_expenses.append(api_expense)

payload["expenses_bank"] = api_output["bank"]

if unmatched_expenses:
    # has unmatched expenses
    payload["unmatched_expenses"] = unmatched_expenses
    payload["notification_email"] = notification_email
    send_task("match_data", payload)

task.complete()