import abstra.workflows as aw
import slack_sdk as slack
import os 
from slack_sdk.errors import SlackApiError

unmatched_expenses = aw.get_data("unmatched_expenses")
expenses_bank = aw.get_data("expenses_bank")

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")
client = slack.WebClient(token=SLACK_BOT_TOKEN)


def slack_msg(message, channel):
    try:
        response = client.chat_postMessage(
            channel=channel,
            text=message
        )
    except SlackApiError as e:
        assert e.response["error"]


message = f'''
:moneybag: *Expense Concilliation Report* :moneybag:

:x: *Unmatched Expenses from {expenses_bank} Bank* :x:
'''
message += '\n'.join([f"- Amount: {expense['amount']}\n- Date: {expense['date']}\n- Currency: {expense['currency']}\n- Justification: {expense['reason']}\n" for expense in unmatched_expenses])

message += '''
:email: *A form was sent to the responsible team. Please review the unmatched expenses using this form and take the necessary actions.* :email:
'''

slack_msg(channel=SLACK_CHANNEL, message=message)


