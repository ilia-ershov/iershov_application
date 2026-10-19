# Deploying to a server

`server-setup.sh` turns a fresh Debian 13 server into a complete installation: the app in Docker, HTTPS, a mail server that forwards aliases, and basic hardening. It reproduces, step by step, a production setup that was configured and verified by hand.

> **Status:** each step mirrors commands that were run and verified on the production server, but the script as a whole has not been run end to end. Read a step before running it, run steps one at a time if in doubt (`sudo ./deploy/server-setup.sh caddy`), and check the output.

## What you need first

1. A Debian 13 server with a public IPv4 address and open ports 22, 25, 80 and 443. Some providers block port 25; ask them to open it.
2. A domain. The examples use `ershov.me` with the service on `veil.ershov.me`.
3. Your SSH public key in `/root/.ssh/authorized_keys` (the script switches SSH to key-only login).

## Run

```bash
git clone https://github.com/ilia-ershov/iershov_application && cd iershov_application
cp deploy/server.env.example deploy/server.env     # set domain, IP, forwarding address...
sudo ./deploy/server-setup.sh                       # or individual steps: sudo ./deploy/server-setup.sh app caddy
```

At the end the script prints the DNS records to create.

## What happens

| Step | Result |
| --- | --- |
| `packages` | Docker, Caddy, Postfix, postsrsd, OpenDKIM, unbound, fail2ban, unattended-upgrades |
| `app` | `.env` with generated secrets, `docker-compose.override.yml`, `docker compose up` |
| `lookup_role` | Read-only DB role for Postfix (5 columns, no password hashes or 2FA secrets) |
| `site` | Personal page on the root domain (`deploy/site/index.html`) |
| `caddy` | HTTPS for the root domain, `www`, the service and `mail.` (Let's Encrypt, automatic renewal) |
| `postfix` | Receives mail for both domains; active aliases from the DB, personal addresses from `/etc/postfix/virtual`; no open relay; postscreen with Spamhaus/SpamCop; SPF check of incoming mail |
| `srs` | Forwarded mail gets an SRS envelope sender so it passes SPF at the destination |
| `dkim` | 2048-bit keys; signs the server's own mail (codes, notifications) |
| `resolver` | unbound on 127.0.0.1 (Spamhaus refuses queries through public resolvers) |
| `postfix_tls` | Postfix uses Caddy's certificate for `mail.` |
| `fail2ban` | Bans SSH/SMTP brute force (your IPs from `F2B_IGNORE` are never banned) |
| `updates` | Daily automatic security updates, no automatic reboot |
| `ssh` | Key-only SSH (skipped if no key is installed) |
| `summary` | Prints the DNS records (incl. DKIM) and the PTR request for the provider |

## Outside the server

These can't be scripted:

- **DNS records** at the registrar: A, MX, SPF, DMARC and DKIM, as printed by the `summary` step.
- **PTR (reverse DNS)** of the server IP pointing to `mail.<domain>`. Ask the hosting provider. Without it, Gmail and iCloud reject or spam forwarded mail.

Certificates are issued as soon as the A records resolve. If `postfix_tls` ran too early, re-run `sudo ./deploy/server-setup.sh postfix_tls`.

## Moving to a new server

Copy these from the old server first so that DNS records and accounts stay valid:

```bash
/etc/opendkim/keys/            # DKIM keys (new keys would need new DNS records)
/etc/postsrsd.secret           # SRS secret
.env                           # app secrets
docker compose exec -T db pg_dump -U mail_organizer mail_organizer > dump.sql
```

Put the files in place, run the script, and restore the database after the `app` step:

```bash
docker compose exec -T db psql -U mail_organizer mail_organizer < dump.sql
```

## Checking the result

```bash
pip install -r live_tests/requirements.txt
BASE_URL=https://veil.example.com MAIL_DOMAIN=veil.example.com SERVER_IP=203.0.113.10 pytest live_tests -v
```

## Files

| File | Purpose |
| --- | --- |
| `server-setup.sh` | The setup script |
| `server.env.example` | Settings template (copy to `server.env`, which is git-ignored) |
| `site/index.html` | Personal page served on the root domain |
| `postfix/lookup-role.sql` | Read-only database role for Postfix |
| `postfix/pgsql-aliases.cf` | Postfix alias lookup query (template) |
| `postfix/main.cf.example` | Minimal Postfix lines for a manual setup |
