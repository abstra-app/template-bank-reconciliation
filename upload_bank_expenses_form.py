import abstra.forms as af
import abstra.workflows as aw
import abstra.tables as at
import os
import shutil
from utils.abstra_ai_prompts import AIPrompts
from abstra.common import get_persistent_dir
import json
import unicodedata
from utils.expenses_entities import ExcelExpense, UnmatchedExpense, MatchedExpense, InternalTrackingExpenses

notification_email = os.getenv("FINANCE_TEAM_EMAIL")

with open('banks.json', encoding='utf-8') as f:
    banks_json = json.load(f)

# Remove accents and tildes from bank labels
for bank in banks_json:
    bank['label'] = unicodedata.normalize('NFKD', bank['label']).encode('ASCII', 'ignore').decode('utf-8')

destination_dir = get_persistent_dir() / 'expenses_files'
destination_dir.mkdir(parents=True, exist_ok=True)
 

def render_input_read(partial):
    bank_dict = partial.get("bank", None)
    if bank_dict:
        return (
            af.Page()
            .read_file("Please upload the expenses file on format .xlsx", key="expenses_file")
        )


expenses_input_page = (
    af.Page()
    .display_markdown(
        '''
# Hello :wave:! 
### :bank: Welcome to the bank expenses conciliation form. Please select the bank and upload the expenses file to start the conciliation process :bank:.
        '''
    ).read_dropdown(
        "Please select the bank",
        banks_json,
        key="bank"
    ).reactive(render_input_read)
    .run("Start processing")
)

for bank in banks_json:
    if bank["value"] == expenses_input_page["bank"]:
        expenses_bank = bank["label"]

expenses_file = expenses_input_page.get("expenses_file", None)

if expenses_file:
    shutil.copy(expenses_file.file.name, os.path.join(str(destination_dir), expenses_file.name))

af.display_markdown('''
<h2 style="text-align: center;">Thank you for uploading the expenses file. We are processing it now.📎</h1>
''')

table_rows = at.select("internal_tracking_expenses", where={"verified": False, "bank": expenses_bank})
database_expenses = [InternalTrackingExpenses(row) for row in table_rows]
excel_expenses = ExcelExpense.read_excel(os.path.join(str(destination_dir), expenses_file.name))

# list of unmatched expenses and matched expenses
unmatched_list: list[UnmatchedExpense] = []
matched_list: list[MatchedExpense] = []

#dictionary of ExcelExpenses associated with possible matches
matching_by_all_mapping = {}
for excel_expense in excel_expenses:
    matching_by_all_mapping[excel_expense.id] = [
        database_expense for database_expense in database_expenses if (
            database_expense.amount == excel_expense.amount 
            and database_expense.currency == excel_expense.currency 
            and (AIPrompts.reason_ai_check(database_expense.reason, excel_expense.reason) or (database_expense.reason == excel_expense.reason))
            and database_expense.date == excel_expense.date
        )
    ]

    if len(matching_by_all_mapping[excel_expense.id]) == 1:
        matched_list.append(MatchedExpense(**{
            "database_expense": matching_by_all_mapping[excel_expense.id][0],
            "excel_expense": excel_expense
        }))
    else:
        unmatched_list.append(UnmatchedExpense(**excel_expense.to_dict()))

if matched_list:
    conciliation_page = MatchedExpense.render_matched_page(matched_list).run("Approve Selected Conciliations")
    approved_list = [details["Id"] for details in conciliation_page["conciliation_approved"]]
else:
    approved_list = []

# list of verified expenses of the database
total_approved_expenses: list[str] = []

for expense in matched_list:
    if str(expense.excel_expense.id) not in approved_list:
        unmatched_list.append(UnmatchedExpense(**expense.excel_expense.to_dict()))
    else:
        total_approved_expenses.append(expense.database_expense.id)

header = (
'''
<h3>❌ The following expenses are mismatched. Please manually verify and try to match with some of the information on the database</h4>
''')

unmatched_page = UnmatchedExpense.render_unmatched_page(unmatched_list, database_expenses, header, approved_list).run(["Use AI to decide", "Approve"])

if unmatched_page.action == "Use AI to decide":
    ai_guess = AIPrompts.use_ai_to_decide(unmatched_list, database_expenses, approved_list)
    unmatched_page = UnmatchedExpense.render_unmatched_page(unmatched_list, database_expenses, header, approved_list, ai_guess).run("Approve")

(overview_page, unaproved_expenses, approved_expenses) = UnmatchedExpense.render_overview_page(unmatched_list, unmatched_page, len(excel_expenses))

overview_page.run("Confirm")

aw.set_data("unaproved_expenses", unaproved_expenses)
aw.set_data("has_unaproved_expenses", str(len(unaproved_expenses) > 0).lower())
aw.set_data("expenses_bank", expenses_bank)

if (len(unaproved_expenses) > 0):
    aw.set_data("notification_email", notification_email)

# updates the database expense status of the approved expenses
total_approved_expenses += approved_expenses
for database_expense in database_expenses:
    if database_expense.id in total_approved_expenses:
        at.update("internal_tracking_expenses", where={"id": database_expense.id}, set={"verified": "true"})

