# FamilyLedger
User can maintain the finacial records of the family like Income, Expenses and Networth..

## Local setup

1. Copy `.env.example` to `.env` in the project root.
2. Set `DATABASE_URL` in `.env` to your MySQL connection, for example
   `mysql://familyledger:your_password@127.0.0.1:3306/family_ledger`.
   Create the database and configure its username and password first.
3. Install dependencies with `pip install -r requirements.txt`, then run
   `python manage.py migrate` and `python manage.py runserver`.
