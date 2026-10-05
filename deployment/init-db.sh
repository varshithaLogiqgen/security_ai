#!/bin/sh
set -eu
PGAPP_PASSWORD=$(cat /run/secrets/app_password)
export PGAPP_PASSWORD
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'SQL'
\getenv app_password PGAPP_PASSWORD
CREATE ROLE secureai_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD :'app_password';
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE secureai TO secureai_app;
SQL
unset PGAPP_PASSWORD
