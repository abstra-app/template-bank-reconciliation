from abstra.ai import prompt
import json

class AIPrompts:

    @staticmethod
    def reason_ai_check(reason_one: str, reason_two: str):
        reason_match = prompt(
            prompt=f"Input (the two reasons described, inputed as a tuple): {(reason_one, reason_two)}",
            instructions=[
                    "You're from the finance team of a company.",
                    "You're evaluating the expenses from the bank that were executed by the employees on the company's credit card.",
                    "You have received two reasons behind two expenses that has the same date and amount",
                    "You need to check if the two reasons are the same or not. So, you need to verify if they refer to the same expense or not based on how the meaning of the reason",
                    "The input will be a tuple with the two reasons that you need to compare.",
                    "Return for me a boolean value that indicates if the two reasons refer to the same expense (True) or not (False)."
            ],    
            format={
                "reason_match": {"type": "boolean", "description": "They refer to the same expense?"}
            },
            temperature=0.1
        )
        return reason_match["reason_match"]
    
    @staticmethod
    def use_ai_to_decide(unmatched_list, expenses_table, approved_list=[]):
        ai_processing_elements = []
        for unmatched_expense in unmatched_list:
            options_list = []
            for database_expense in expenses_table:
                if (database_expense.date == unmatched_expense.date) and (database_expense.format_return() not in approved_list):
                    options_list.append(database_expense.to_dict())
            ai_processing_elements.append((unmatched_expense.to_dict(), options_list))
        try:
            ai_processing = prompt(
                prompt=f"Input (List of Tuples as described): {ai_processing_elements}",
                instructions=[
                    "You're from the finance team of a company.",
                    "You're evaluating the expenses from the bank that were executed by the employees on the company's credit card.",
                    "Some expenses in the credit card extract are not matching with the expenses in the database registered by the finance team.",
                    "You need to match the expenses from the bank with the expenses in the database if you think they are the same but with little information mismatches.",
                    "You need to choose the best expense that matches the one from the bank.",
                    "The input will be a list of tuples, each tuple will have the unmatched expense as the first element and a list of options to match with the unmatched expense as the second element.",
                    "You need to return a list of dictionaries where each dictionary represents an expense from the credit card extract.",
                    "The dictionary key should be the credit card extract expense id, and the value should be the id of the expense from the database that best matches the credit card extract expense.",
                    "If you think that the credit card extract expense does not match with any of the expenses in the database, you need to return the credit card extract expense id with the value 'None'."
                    "Additionaly, if you cant find the expense in the database (in other words, if you return the value None for the id), return the reason why you couldnt find the expense in the database (as the variable unmatch_reason). Pick one, or more than one, between the following options for the unmatch reason:",
                    "1. The expense is not in the database",
                    "2. The expense is in the database but with a different amount",
                    "3. The expense is in the database but with a different reason",
                    "4. The expense is in the database but with a different currency",
                    "If you found the expense in the database, return None as the unmatch reason."
                ],
                format={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "credit_card_expense_id": {"type": "string"},
                            "match_db_expense_id": {"type": "string"},
                            "unmatch_reason": {"type": "string"}
                        },
                        "required": ["credit_card_expense_id", "match_db_expense_id", "unmatch_reason"]
                    }
                },
                temperature=0.1
            )
        except:
            ai_processing = {}

        # Ensure the 'items' key is a proper string and remove newlines
        if 'items' in ai_processing and isinstance(ai_processing['items'], str):
            ai_processing['items'] = ai_processing['items'].replace('\n', '')

        # Convert the cleaned string back to a Python object if necessary
        if ai_processing.get('items'):
            ai_processing['items'] = json.loads(ai_processing['items'])
            return ai_processing.get("items", [])
        return []
