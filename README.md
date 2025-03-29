# Bank Reconciliation Template
## How it works:

This project includes an expense reconciliation system built with Abstra and Python scripts. Expenses are automatically imported from the bank's API and undergo an automated reconciliation process with the expenses registered in the database. If any expenses fail the automatic verification, a alert is sent on Slack and a form is sent to the responsible team for manual approval, assisted by Abstra AI. Additionally, expenses can be manually uploaded as an .xlsx file (see the attached example in this repository) through a designated form and reconciled using the information available in the database. For any unreconciled expenses, the responsible team has the option to register them in the database. 

Integrations:
  - Slack
  - Inter Bank
  - Brex Bank
  - Santander Bank
  - Clara Bank

To customize this template for your team and build a lot more, [book a demonstration here.](https://meet.abstra.app/demo?url=template-bank-reconciliation)

![image](https://github.com/user-attachments/assets/7765478e-5e38-4ad4-b169-4b7ba0195b1a)

## Initial Configuration
To use this project, some initial configurations are necessary:

1. **Python Version**: Ensure Python version 3.9 or higher is installed on your system.
2. **Environment Variables**:

   The following environment variables are required for both local development and online deployment:
    1. Santander Bank
       - `SANTANDER_ACC_NUMBER`: Santander bank account number from which you want to import the expenses
       - `SANTANDER_BANK_ID`: Santander bank Employer Identification Number (EIN)
       - `SANTANDER_API_KEY`: Santander authentication key to import the expenses using the API service
    2. Inter Bank
       - `INTER_ACC_NUMBER`: Inter bank account number from which you want to import the expenses
       - `INTER_API_KEY_PATH`: Path to Inter authentication key file (.key) provided by the bank and used for validation when using the API
       - `INTER_CLIENT_ID`: Inter application ID used to generate the access token
       - `INTER_CLIENT_SECRET`: Inter application secret used to generate the access token
    3. Brex Bank
       - `BREX_API_KEY`: Brex authentication key to import the expenses using the API service
    4. Clara Bank
       - `CLARA_CERTIFICATION_PATH`: Path to Clara certification file (.pem) provided by the bank and used for validation when using the API
       - `CLARA_API_KEY_PATH`: Path to Clara authentication key file (.key) provided by the bank and used for validation when using the API
       - `CLARA_CLIENT_ID`: Clara application ID used to generate the access token
       - `CLARA_CLIENT_SECRET`: Clara application secret used to generate the access token
    6. Certification Path
       - `CERTIFICATION_PATH`: Path to the company certificate emitted by responsible institutions (.crt)
    7. Slack 
       - `SLACK_BOT_TOKEN`: The slack validation token used to access the API and send alerts
       - `SLACK_CHANNEL`: The slack channel to send the unmatched expeses alerts
    8. Notification email 
       - `FINANCE_TEAM_EMAIL`: Email of the team responsible for approving the expenses

   For local development, create a `.env` file at the root of the project and add the variables listed above (as in `.env.example`). For online deployment, configure these variables in your [environment settings](https://docs.abstra.io/cloud/envvars).

3. **Dependencies**: To install the necessary dependencies for this project, a `requirements.txt` file is provided. This file includes all the required libraries.

   Follow these steps to install the dependencies:
   
   1. Open your terminal and navigate to the project directory.
   2. Run the following command to install the dependencies from `requirements.txt`:
        ```sh
        pip install -r requirements.txt
        ```
4. **Access Control**: The generated form is protected by default. For local testing, no additional configuration is necessary. However, for cloud usage, you need to add your own access rules. For more information on how to configure access control, refer to the [Abstra access control documentation](https://docs.abstra.io/concepts/access-control).

5. **Database configuration**: Set up your database tables in Abstra Cloud Tables according to the schema defined in `abstra-tables.json`.
   
    To automatically create the table schema, follow these steps:
  
    1. Open your terminal and navigate to the project directory.
  
    3. Run the following command to install the table schema from `abstra-tables.json`:
       ```sh
       abstra restore
       ```
       
    For guidance on creating and managing tables in Abstra, refer to the [Abstra Tables documentation](https://docs.abstra.io/cloud/tables).
  
6. **Local Usage**: To access the local editor with the project, use the following command:

   ```sh
      abstra editor path/to/your/project/folder/
   ```

## General Workflow:
To implement this system use the following scripts:

### Expenses Import
For importing the expenses from the bank`s APIs, use:
  - **get_expenses_from_carla_api.py**: Script to import the expenses data from Clara API.
  - **get_expenses_from_inter_api.py**: Script to import the expenses data from Inter API.
  - **get_expenses_from_santander_api.py**: Script to import the expenses data from Santander API.
  - **get_expenses_from_brex_api.py**: Script to import the expenses data from Brex API.

### Automatic Bank Reconciliation
  - **match_expenses.py**: Script to automatically verify imported expenses against those registered in the database.

### Slack Notification
  - **expenses_slack_notifcation.py**: Script to send an alert to a Slack channel regarding the unreconciled expenses resulting from the automatic matching process.

### Manual Bank Reconciliation Form
  - **manual_bank_reconciliation.py**: Script to generate a form for verifying unmatched expenses and matching them with expenses in the database.

### Manual Upload of Bank Expenses Form
  - **upload_bank_expenses_form.py**: Script to generate a form for uploading expenses as an .xlsx file (use `Bank_Expenses.xlsx` as a template) and verifying them against the expenses registered in the database.

### Database Bank Expense Fix/Registration Form
  - **register_missing_expenses_form.py**: Script to register missing expenses in the database or update existing expenses to align with the information from the API or spreadsheet.


If you're interested in customizing this template for your team in under 30 minutes, [book a customization session here.](https://meet.abstra.app/demo?url=template-bank-reconciliation)
