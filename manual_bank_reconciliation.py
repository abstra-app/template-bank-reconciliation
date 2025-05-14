import abstra.forms as af
from abstra.tasks import get_tasks, send_task
import abstra.tables as at
from utils.expenses_entities import UnmatchedExpense, InternalTrackingExpenses
from utils.abstra_ai_prompts import AIPrompts

tasks = get_tasks()
for task in tasks:
    payload = task.payload
    notification_email = payload["notification_email"]
    unmatched_expenses = payload["unmatched_expenses"]
    expenses_bank = payload["expenses_bank"]

    table_rows = at.select("internal_tracking_expenses", where={"verified": False, "bank": expenses_bank})
    database_expenses = [InternalTrackingExpenses(row) for row in table_rows]

    unmatched_list = []
    for unmatched_expense in unmatched_expenses:
        unmatched_list.append(UnmatchedExpense(**unmatched_expense))

    header = (f'''
<h2 style="text-align: center;">🔍Expense Conciliation Report🔎</h1>
<h4 style="text-align: center;">Please verify the following unmatched expenses from bank {expenses_bank} and compare it with the expenses on the database.</h3>
''')

    unmatched_page = UnmatchedExpense.render_unmatched_page(unmatched_list, database_expenses, header).run(["Use AI to decide", "Approve"])

    if unmatched_page.action == "Use AI to decide":
        ai_guess = AIPrompts.use_ai_to_decide(unmatched_list, database_expenses)
        unmatched_page = UnmatchedExpense.render_unmatched_page(unmatched_list, database_expenses, header, approved_list=[], ai_guess=ai_guess).run("Approve")

    overview_page = af.Page().display_markdown(f'''
<h2 style="text-align: center;">📃 Conciliation Completed 📃</h1>
''')

    (overview_page, unaproved_expenses, approved_expenses) = UnmatchedExpense.render_overview_page(unmatched_list, unmatched_page, len(api_output["data"]), from_api=True)

    overview_page.run("Confirm")


    # updates the database expense status of the approved expenses
    for database_expense in database_expenses:
        if database_expense.id in approved_expenses:
            at.update("internal_tracking_expenses", where={"id": database_expense.id}, set={"verified": "true"})

    if(len(unaproved_expenses) > 0):
        payload["unaproved_expenses"] = unaproved_expenses
        send_task("unaproved_expenses", payload)

    task.complete()