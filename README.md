# Audit Leads Agent

Scant elke avond om **23:00 Europe/Amsterdam** een set Nederlandse opdrachten- en aanbestedingenplatformen op audit-gerelateerde freelance opdrachten en stuurt elke nieuwe lead als losse mail naar OmniFocus Mail Drop, zodat ze als taak in je inbox landen.

## Bronnen (fase 1)

| Bron | Type | Status |
|---|---|---|
| TenderNed | RSS-feed | Stabiel |
| Freelance.nl | HTML-scrape | Selectors te tunen |
| Hoofdkraan.nl | HTML-scrape | Selectors te tunen |
| Jellow | HTML-scrape | Selectors te tunen |
| Striive | HTML-scrape | Selectors te tunen |
| ZZP-Markt | HTML-scrape | Selectors te tunen |
| Inhuurdesk | HTML-scrape | Selectors te tunen |
| Planet Interim | HTML-scrape | Selectors te tunen |

> **Let op:** voor de HTML-scrapers zijn de CSS-selectors een best-effort startpunt. Sites herzien hun frontend regelmatig. Draai eerst `python run.py --dry-run --force --debug` lokaal of via `workflow_dispatch` met `dry_run=true` en bekijk de logs — als een bron 0 items oplevert, moet je in `scrapers/<bron>.py` de `select(...)` calls aanpassen aan de huidige DOM.

## Setup

### 1. Repo aanmaken op GitHub

```bash
cd /Users/janwillemwalravens/audit-leads-agent
gh repo create audit-leads-agent --private --source=. --remote=origin --push
```

(of maak handmatig een lege private repo, daarna `git remote add origin ... && git push -u origin main`)

### 2. GitHub Secrets

In de repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Waarde |
|---|---|
| `OMNIFOCUS_MAILDROP` | `janwillemwalravens.rg8gr@sync.omnigroup.com` |
| `SMTP_HOST` | bv. `smtp.gmail.com` of jouw mailserver |
| `SMTP_PORT` | `587` (STARTTLS) of `465` (SSL) |
| `SMTP_USER` | het mailaccount waarmee je inlogt |
| `SMTP_PASS` | wachtwoord of app-password |
| `SMTP_FROM` | afzenderadres (bv. `janwillem.walravens@wi-solutions.nl`) |
| `EMAIL_CC` | *(optioneel)* bcc/cc adres voor archief |

**Gmail tip:** zet 2FA aan en gebruik een [App Password](https://myaccount.google.com/apppasswords) als `SMTP_PASS`.

### 3. Workflow aanzetten

Bij de eerste push activeert GitHub Actions automatisch. Test 'm meteen via:

- Repo → **Actions → Daily audit-leads scan → Run workflow** → kies `dry_run = true`.

Dit logt wat hij gevonden zou hebben zonder mails te sturen. Daarna draait hij elke dag om 23:00 NL.

### 4. Lokaal testen

```bash
cd /Users/janwillemwalravens/audit-leads-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py --dry-run --force --debug
```

## Hoe filtering werkt

Alleen opdrachten met audit-gerelateerde trefwoorden (zie `filter.py`) worden doorgelaten. De lijst is makkelijk uit te breiden — voeg een term toe aan `KEYWORDS` en commit.

## Dedup

`state/seen.json` houdt URLs bij die we al gezien hebben (60 dagen retentie). De GitHub Action commit dit bestand terug naar de repo na elke run, zodat dezelfde lead nooit twee keer in OmniFocus belandt.

## Een bron uitschakelen

Zet `enabled = False` in de betreffende `scrapers/<bron>.py`.

## Een bron toevoegen

1. Maak `scrapers/<naam>.py` aan, subclass `Scraper`, implementeer `scrape()` en yield `Opportunity(...)` objecten.
2. Voeg de class toe aan `scrapers/__init__.py` (`ALL_SCRAPERS`).
3. Klaar.

## Troubleshooting

- **0 items van een site:** selectors verouderd. Open de site in een browser, inspecteer de listings, pas `select(...)` aan in de scraper.
- **GitHub Action faalt op SMTP:** check de secrets; voor Gmail moet je echt een App Password gebruiken (geen normaal wachtwoord).
- **GitHub pauzeert scheduled runs na 60 dagen inactiviteit:** push iets kleins (bv. een README-edit) of trigger handmatig om 'm wakker te houden.
- **Mails komen niet aan in OmniFocus:** check op https://sync.omnigroup.com of Mail Drop nog actief is, en kijk in spam.
