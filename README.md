# Veil — one e-mail address per website

**Live:** https://veil.ershov.me/

Veil gives you a separate, randomly generated e-mail address for every website
you sign up to. Mail sent to that address is forwarded to your real inbox, and
you can switch any address off with one click.

It started as my graduation research project at HSE Lyceum (*"Mail Organizer"*,
2024–2026). The original project documents are in Russian and are kept in this
repository (see [Project documents](#project-documents)).

<!-- Screenshots: add PNGs to docs/screenshots/ and uncomment.
![Dashboard](docs/screenshots/dashboard.png)
![Create address](docs/screenshots/create.png)
-->

## Why

When you use one address everywhere, it ends up in leaked databases. Attackers
then use it to send spam and phishing, and to look up which services you are
registered on, which makes targeted phishing more convincing. Unsubscribing is
often hard, and changing your main address means updating it on every site.

With one alias per site:

- a leaked address tells an attacker nothing about your other accounts;
- you can see which service leaked or sold your address, and turn it off;
- changing your real inbox is a single setting, not dozens of sites;
- aliases are receive-only, so they cannot be abused to send mail.

Existing tools cover part of this: DuckDuckGo Email Protection has no
management panel, Apple *Hide My Email* needs iCloud+ or an Apple device, and
temporary-mail sites expire within hours or show your mail to anyone.

## Features

- Account sign-up with an e-mail confirmation code; passwords hashed with bcrypt
- Random alias generation; the server signs every generated name with HMAC so a
  client cannot register an alias it did not receive from the server
- Label each alias with the service it is used for and a link to it
- Deactivate and reactivate aliases; deactivated ones are listed separately
- Change the main (forwarding) address
- Delete the account together with all aliases
- Help section with advice on phishing, passwords, compromised accounts and
  digital hygiene

## Architecture

| Part | Stack |
| --- | --- |
| Backend API | Python, Flask, SQLAlchemy, PostgreSQL (JSONB), JWT (HS256), bcrypt |
| Frontend | React 19, React Router, Vite, Axios |

```
project/
  app.py       Flask API: auth, aliases, deactivation, account management
  models.py    SQLAlchemy models: users, emails (aliases), deactivated
  front/       React single-page app (pages/: Home, Signup, Login, Dashboard,
               CreateMailAdress, Deactivated, changeEmail, help)
```

## Running locally

Backend (needs PostgreSQL):

```bash
cd project
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cat > .env <<'ENV'
DATABASE_URL=postgresql://user:password@localhost/veil
SECRET_KEY=<long random string>
ENV
python app.py            # serves the API on :5000
```

Frontend:

```bash
cd project/front
npm install
VITE_API_URL=http://localhost:5000 npm run dev
```

## Project documents

Written in Russian for the lyceum research project:

| File | Contents |
| --- | --- |
| `final_application.md` | Project proposal: problem, audience, requirements, analogues, plan, risks |
| `final_scripts.md` | User scenarios (sign-up, aliases, deactivation, account deletion, help) |
| `ИВР отчет.doc` | Final research report |

## Author

Ilia Ershov — [github.com/ilia-ershov](https://github.com/ilia-ershov)
