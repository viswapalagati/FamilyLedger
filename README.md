# FamilyLedger

FamilyLedger helps families maintain records of income, expenses, and net worth.

## Local setup

1. Copy `.env.example` to `.env` in the project root.
2. Install the pinned dependencies with `python -m pip install -r requirements.txt`.
   Keep the installed Django version aligned with this file; this project pins
   Django 5.2.17.
3. Set `DATABASE_URL` in `.env` to a local MySQL database. Create the database
   and configure its username and password first. If you use Django 6.1 locally,
   MySQL 8.4 or newer is required; alternatively, use the pinned dependencies.
4. Run `python manage.py migrate` and `python manage.py runserver`.

## Render / PostgreSQL

Set Render's `DATABASE_URL` environment variable to the PostgreSQL connection
URL for the Render database. The same Django setting selects the backend from
the URL, so do not commit database credentials or replace the local `.env`
file with production credentials. Install dependencies from `requirements.txt`
and run `python manage.py migrate --noinput` against the production database
when deploying a schema change.

The ORM and migrations are used for both databases. Test important changes
against PostgreSQL as well as local MySQL: MySQL does not support the conditional
unique index used to prevent duplicate top-level account heads, while PostgreSQL
does.
