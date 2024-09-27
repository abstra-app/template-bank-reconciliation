import abstra.workflows as aw
import abstra.tables as at
import os 
from utils.abstra_ai_prompts import AIPrompts
from utils.expenses_entities import InternalTrackingExpenses

notification_email = os.getenv("FINANCE_TEAM_EMAIL")

api_output = aw.get_data("api_output")
expenses_bank=aw.get_data("expenses_bank")
api_output_data = api_output["data"]
api_output_bank = api_output["bank"]

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

aw.set_data("expenses_bank", api_output["bank"])

if unmatched_expenses:
    aw.set_data("has_unmatched_expenses", True)
    aw.set_data("unmatched_expenses", unmatched_expenses)
    aw.set_data("notification_email", notification_email)
else:
    aw.set_data("has_unmatched_expenses", False)