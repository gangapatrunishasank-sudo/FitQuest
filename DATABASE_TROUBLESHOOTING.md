# FitQuest AI — Database & Login Fix

The production build uses PostgreSQL whenever `DATABASE_URL` is present. Local development uses SQLite automatically.

## Render requirement

The web service must have this environment variable:

`DATABASE_URL`

Its value must be the **Internal Database URL** of the Render PostgreSQL database in the same Render region as the web service.

Do not paste the database password into the GitHub repository.

## What the fixed authentication flow does

1. Creates the user in PostgreSQL.
2. Immediately reads the user back from PostgreSQL.
3. Creates a 30-day session token.
4. Stores only the SHA-256 hash of that token in PostgreSQL.
5. Stores the authenticated user in Streamlit session state.
6. Keeps a browser query-parameter fallback for refreshes.
7. Revalidates the user against PostgreSQL on every page load.

If account creation succeeds but the user cannot be read back, the application now reports that as a database error instead of silently behaving like a failed login.

## Important for an existing deployment

If an older version of FitQuest created accounts in SQLite before PostgreSQL was connected, those accounts are **not automatically present in PostgreSQL**. Create a fresh account on the live Render site after the fixed build is deployed.

The local file `data/fitquest.db` is intentionally ignored by Git.
