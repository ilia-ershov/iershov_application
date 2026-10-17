-- Read-only database role for Postfix: it can resolve an active alias to its owner's
-- main address and nothing else (no password hashes, no 2FA secrets).
-- Run as a superuser in the application database:  psql -d mail_organizer -f lookup-role.sql
CREATE ROLE postfix_lookup LOGIN PASSWORD 'change-me';
GRANT CONNECT ON DATABASE mail_organizer TO postfix_lookup;
GRANT USAGE ON SCHEMA public TO postfix_lookup;
GRANT SELECT (uuid, email) ON users TO postfix_lookup;
GRANT SELECT (user_id, local_part, is_active) ON aliases TO postfix_lookup;
