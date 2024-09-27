import abstra.forms as af
import abstra.workflows as aw
import abstra.tables as at
from utils.expenses_entities import InternalTrackingExpenses

unaproved_expenses = aw.get_data("unaproved_expenses")
expenses_bank = aw.get_data("expenses_bank")
table_rows = at.select("internal_tracking_expenses", where={"verified": False})
database_expenses = [InternalTrackingExpenses(row) for row in table_rows]
unaproved_expenses_id = []

# define the actions that can be taken on the unaproved expenses
def encapsulate_actions(unaproved_expense):
    '''
    Encapsulates the actions that can be taken on the unaproved expenses
    The options are Register in the database, Correct the database and Ignore
    '''
    expense_id = unaproved_expense["id"]
    def __actions_options(partial):
        if partial:
            if expense_id in partial.keys():
                if partial[expense_id] == 'Register in the database':
                    return (
                        af.Page()
                        .display_markdown(f'''
**Please fill the fields below with the expense information**
                        ''')
                        .read_date("Date", key=f"date", initial_value = unaproved_expense["date"])
                        .read("Amount", key=f"amount", initial_value = unaproved_expense["amount"])
                        .read("Currency", key=f"currency", initial_value = unaproved_expense["currency"])
                        .read("Reason", key=f"reason", initial_value = unaproved_expense["reason"])
                    )
                elif partial[expense_id] == 'Correct the database':
                    database_options = [{"label":database_expense.format_return(), "value": database_expense.id} for database_expense in database_expenses if database_expense.date == unaproved_expense["date"]]
                    output_page = (
                        af.Page()
                        .display_markdown(f'''
**Please select one of the database information to correct and fix the fields related to this expense**
                        ''')
                    )
                    if database_options:
                        output_page = output_page.read_dropdown("Select the database expense", database_options, key=f"database_expense_ref") 
                        output_page = (
                            output_page
                            .read_date("Date", key=f"date", initial_value = unaproved_expense["date"])
                            .read("Amount", key=f"amount", initial_value = unaproved_expense["amount"])
                            .read("Currency", key=f"currency", initial_value = unaproved_expense["currency"])
                            .read("Reason", key=f"reason", initial_value = unaproved_expense["reason"])
                        )
                    else:
                        output_page = output_page.display_markdown("**⚠️There are no expenses available to correct⚠️**")
                    return output_page
                elif partial[expense_id] == 'Ignore':
                    pass
    return __actions_options

# render the initial page
initial_page = af.Page().display_markdown(f'''
<h2 style="text-align: center;">✏️ Expenses Registration and Correction</h1>

Verify the following unconciliated expenses and register them in the database or correct the database to match it. 
''').run(['Add All Expenses to Database', 'Verify Each Expense'])

if initial_page.action == 'Add All Expenses to Database':
    for expense in unaproved_expenses:
        expense["bank"] = expenses_bank
    at.insert("internal_tracking_expenses", unaproved_expenses)

if initial_page.action == 'Verify Each Expense':
    # renders one page for each expense with the options to register, correct or ignore it
    page_list = []
    for unaproved_expense in unaproved_expenses:
        unaproved_expenses_id.append(unaproved_expense["id"])
        page_list.append(
            af.Page().display_markdown(
            f'''
    - Date: {unaproved_expense["date"]}
    - Amount: {unaproved_expense["amount"]}
    - Currency: {unaproved_expense["currency"]}
    - Reason: {unaproved_expense["reason"]}
            '''
            ).read_multiple_choice(
            "What do you want to do?",
            ["Register in the database", "Correct the database", "Ignore"],
            key=unaproved_expense["id"]
            ).reactive(encapsulate_actions(unaproved_expense))
        )

    steps_response = af.run_steps(page_list)

    # based on the actions selected for each expense, proceeds to insert on the database, update the database or ignore the expense
    if steps_response: 
        for response in steps_response:
            action_keys = set(response.keys()) & set(unaproved_expenses_id)

            if not action_keys:
                continue

            action_key = action_keys.pop()
            if response[action_key] == "Register in the database":
                insert_fields = {
                    "date": response["date"],
                    "amount": response["amount"],
                    "currency": response["currency"],
                    "reason": response["reason"],
                    "verified": True,
                    "bank": expenses_bank
                }
                at.insert("internal_tracking_expenses", insert_fields)
            elif response[action_key] == "Correct the database":
                database_expense_id_ref = response["database_expense_ref"]
                change_fields = {
                    "date": response["date"],
                    "amount": response["amount"],
                    "currency": response["currency"],
                    "reason": response["reason"],
                    "verified": True,
                    "bank": expenses_bank
                }
                at.update("internal_tracking_expenses", 
                          where={"id": database_expense_id_ref},
                          set=change_fields)
            else:
                pass