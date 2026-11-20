# GB Language Centre — TCF Canada January 2027 checker

This is a **separate GitHub Actions workflow** from the December 2026 checker. It independently monitors [the public GBLC booking calendar](https://gblc.ca/en/book-now/choose-date?test=6) for **January 1–31, 2027**, inclusive.

## What it checks

- TCF Canada – Computer, Toronto, session cards containing an actual exam date, positive observed seat count, a Select action, and a corroborating positive-slot date button.
- Excludes other months, past dates, expected result dates, and expired registration deadlines.
- Never signs in, buys, books, uploads documents, or attempts to evade anti-bot checks.
- Records previously observed sessions in a separate repository issue titled `[TCF January Monitor] Internal state (do not close)`.
- Creates an alert issue titled `[TCF JAN SLOT] ...` only when a qualifying session newly appears or reappears.
- On initial production check, reports **all currently available January 2027 sessions** in one issue; later alerts only contain newly detected sessions.
- After **three consecutive scan errors**, creates a separate `[TCF JANUARY] Three consecutive failed checks` issue.
- Does not access GBLC after January 31, 2027 (Toronto date). Disable the workflow after you book or the date window passes.

## Schedule

Workflow file: `.github/workflows/tcf-january.yml`.

Checks **every 30 minutes** at UTC minutes `02` and `32`. The December checker runs every 5 minutes. GitHub scheduling is best effort and runs can be delayed. GitHub Actions scheduling is best effort and may be delayed or occasionally skipped.

[Open January workflow](https://github.com/harjotsingh5281/gpt-test/actions/workflows/tcf-january.yml).

## Notifications

GitHub Issues are created and assigned to `harjotsingh5281`. GitHub can suppress self-generated assignment notifications, so do **not** assume a push reaches your phone. A separate direct ntfy channel is implemented:

- Prefer GitHub Actions repository secret `NTFY_TOPIC_JANUARY` to keep January push alerts separate.
- If absent, the January checker falls back to `NTFY_TOPIC` (shared with December).
- Either secret must contain only a hard-to-guess 16–64-character topic name using letters, numbers, hyphens, or underscores.
- Subscribe to the same topic in the ntfy Android app and allow app notifications.
- For a safe test, open the January workflow, choose **Run workflow**, check `notification_test=true`. It sends one push without checking GBLC. Do not put the topic name in a GitHub issue or public repository.
- The January monitor also supports optional `DISCORD_WEBHOOK_URL`, inherited from the December monitor.

**Important:** Direct email delivery has **not** been configured. GitHub issue alerts and ntfy/Discord are implemented. If a notification service isn't configured, slot issues still provide an audit trail.

## Live verification (November 20, 2026)

GitHub Actions live dry run #44808345023 completed successfully and found **26 January 2027 sessions on 15 exam dates** (January 6, 15–17, 19–24, 27–31). Availability can change rapidly and no spot is reserved.
