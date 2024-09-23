import uuid
import pandas as pd
from datetime import date
import abstra.forms as af
from typing import List, Tuple


class InternalTrackingExpenses:
    def __init__(self, row):
        self.id = row["id"]
        self.amount = row["amount"]
        self.currency = row["currency"]
        self.bank = row["bank"]
        self.date = row["date"]
        self.reason = row["reason"]
        self.verified = row["verified"]

    def to_dict(self):
        return {key: value for key, value in self.__dict__.items() if not key.startswith('_')}

    def format_return(self):
        return f"{self.amount} \\{self.currency} \\{self.reason} \\{self.date}"


class ExcelExpense:
    def __init__(self, id: uuid, amount: float, currency: str, bank: str, date: date, reason: str):
        self.id = id
        self.amount = amount
        self.currency = currency
        self.bank = bank
        self.date = date
        self.reason = reason

    @staticmethod
    def read_excel(path: str) -> list:
        return [
            ExcelExpense(
                id=str(uuid.uuid4()),
                amount=row["amount"],
                currency=row["currency"],
                bank=row["bank"],
                date=row["date"].strftime("%Y-%m-%d"),
                reason=row["reason"]
            ) for row in pd.read_excel(path).to_dict("records")
        ]
    
    def format_return(self) -> str:
        return f"{self.amount} \\ {self.currency} \\ {self.reason} \\ {self.date}"
    
    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "amount": self.amount,
            "currency": self.currency,
            "bank": self.bank,
            "date": self.date,
            "reason": self.reason
        }


class MatchedExpense:
    def __init__(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


    @staticmethod
    def _parse_to_dataframe(matched_list):
        output_df = pd.DataFrame(columns=["Bank Expense Details", "Database Expense Details"])
        for matched in matched_list:
            output_df = pd.concat([
                output_df,
                pd.DataFrame({
                    "Id": [str(matched.excel_expense.id)],
                    "Bank Expense Details": [matched.excel_expense.format_return()],
                    "Database Expense Details": [matched.database_expense.format_return()]
                })
            ], ignore_index=True)
        return output_df

    @staticmethod
    def render_matched_page(matched_list) -> af.Page:
        matched_page = (
            af.Page()
            .display_markdown('''
<h3>⚠️ The following information shows the data concilliated between the bank expenses and the database expenses (Amount, Currency, Reason and Date). Please verify the matches and approve/reject each of them.</h3>                      
            ''') 
            .read_pandas_row_selection(MatchedExpense._parse_to_dataframe(matched_list), key="conciliation_approved", multiple=True, required=False)       
        )

        return matched_page


class UnmatchedExpense:
    def __init__(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        return {
            "id": str(self.id),
            "amount": self.amount,
            "currency": self.currency,
            "reason": self.reason,
            "date": self.date
        }
    
    @staticmethod
    def render_unmatched_page(unmatched_list, expenses_table, header, approved_list=[], ai_guess=[]) -> af.Page:
        unmatched_page = (
            af.Page()
            .display_markdown(header)
        )
        counting = 1
        for unmatched_expense in unmatched_list:
            # defines which guess the ai did for the unmatched expense (by id)
            for ai_unmatched_expense in ai_guess:
                if ai_unmatched_expense["credit_card_expense_id"] == unmatched_expense.id:
                    ai_guess_id = ai_unmatched_expense["match_db_expense_id"]
                    ai_unmatch_reason = ai_unmatched_expense["unmatch_reason"]
                    ai_initial_value = "None"

            # defines the dropdown options for the unmatched expense
            dropdown_options = [{"label": "None", "value": "None"}]
            for internal_expense in expenses_table:
                if (internal_expense.date == unmatched_expense.date) and (internal_expense.format_return() not in approved_list):
                    dropdown_options += [{"label": internal_expense.format_return(), "value": internal_expense.id}]

                # defines the ai guess value for the unmatched expense to set it as initial value in the dropdown
                if ai_guess and internal_expense.id == ai_guess_id:
                    ai_initial_value = internal_expense.id 

            unmatched_page = (
                unmatched_page
                .display_markdown(
                    f'''
```
Expense {counting}:
- Amount: {unmatched_expense.amount}
- Currency: {unmatched_expense.currency}
- Reason: {unmatched_expense.reason}
- Date: {unmatched_expense.date}
```
                '''
                )
                .read_dropdown(
                    "Choose the best expense that matches the one from the bank (Amount \\ Currency \\ Reason \\ Date) " + (f"[There was no conciliation because: {ai_unmatch_reason}]" if ai_guess and ai_unmatch_reason not in (None, 'None') and ai_guess_id in (None, 'None') else ""),
                    dropdown_options,
                    key=unmatched_expense.id,
                    required=False,
                    full_width=True,
                    initial_value = ai_initial_value if ai_guess else "None"
                )
            )

            counting+=1
        return unmatched_page

    @staticmethod
    def render_overview_page(unmatched_list, unmatched_page, total_sample, from_api=False) -> Tuple[af.Page, List, List]:

        overview_page = af.Page().display_markdown(f'''
<h2 style="text-align: center;">📃 Conciliation Completed 📃</h1>
    ''')
        unaproved_expenses = []
        approved_expenses = []
        first_loop = 0
        
        for unmatch_expense in unmatched_list:
            if unmatched_page[unmatch_expense.id] == "None":
                if first_loop == 0:
                    overview_page = overview_page.display_markdown(f'''
<h3>Overview of Unconciliated Expenses:</h3>                         
                    ''')
                    first_loop = 1
                unaproved_expenses.append(unmatch_expense.to_dict())
                overview_page = overview_page.display_markdown(
                    f'''
    - Amount: {unmatch_expense.amount}  
    - Currency: {unmatch_expense.currency}
    - Reason: {unmatch_expense.reason}
    - Date: {unmatch_expense.date}
    - Status: Unmatched
                    ''')
            else:
                approved_expenses.append(unmatched_page[unmatch_expense.id])
        overview_page.display_markdown(f'''
<h3>Balance:</h3>\n
        - Total Unmatched Expenses: {len(unaproved_expenses)} \n
        - Total Matched Expenses: {total_sample - len(unaproved_expenses)}\n                                           
        '''+ (
        f'''
        - Total Expenses Matched Automatically: {total_sample - len(unaproved_expenses) - len(approved_expenses)}\n
        - Total Expenses Matched Manually: {len(approved_expenses)}\n
        ''' if from_api else ""
            )
        ).display_markdown(f'''**An email will be sent to the finance team with the list of unapproved expenses (if any) and the actions that can be taken.**''')
        return (overview_page, unaproved_expenses, approved_expenses)
    

