# GBLC TCF Canada slot monitor

**Status:** Scheduled cloud monitoring enabled. This is a read-only booking-calendar observer, not a booking bot.

**Exam:** TCF Canada – Computer, GB Language Centre, Toronto. **Target exam dates:** December 10–31, 2026 (inclusive).

Official booking page: https://gblc.ca/en/book-now/choose-date?test=6

The monitor never signs in, uploads passports, reserves dates, or makes payments. An alert means a matching session was visible during the check, **not** that a seat was held.

## Schedule and verified test

GitHub Actions schedule: `7,22,37,52 * * * *` (every 15 minutes, UTC clock). GitHub may delay or skip scheduled runs, especially at busy times. This schedule uses the **cloud**, so your laptop need not be running.

A successful live GitHub dry run on November 20, 2026 (run #44801384024) parsed **123 examination cards** and found **0 eligible dates**. It used Ubuntu 24.04 and a Playwright Chromium browser. Actual GitHub scan execution is not guaranteed to be immediate.

Open the [Actions workflow](https://github.com/harjotsingh5281/gpt-test/actions/workflows/tcf-monitor.yml) to review live and scheduled runs.

## Notifications

**GitHub Issues:** When an eligible TCF Canada session appears or reappears, the monitor creates a GitHub issue assigned to the repository owner, listing exact exam date/time, observed seat count, and a manual booking link. Enable assignment notifications in [GitHub notification settings](https://github.com/settings/notifications) and the GitHub mobile app. Internal monitoring state is kept in a GitHub issue named **[TCF Monitor] Internal state (do not close)**. Do not close or edit it.

**Optional immediate Discord push:** In GitHub go to **Settings → Secrets and variables → Actions → New repository secret**. Set the name to `DISCORD_WEBHOOK_URL` and paste a Discord channel webhook URL as its value. Never put it in a commit, issue, or chat message. Discord sends the same booking/failure alert; the secret is optional.

**Failure alerts:** If the read-only checker fails three consecutive scans, it creates a separate GitHub failure issue. A broken GitHub schedule that never starts jobs requires independent heartbeat monitoring; this workflow alone cannot detect the absence of its own runs.

## Recommended Android push notifications with ntfy

GitHub Issue assignment pushes can be suppressed for self-created activity. As a direct, optional alternative, the monitor supports **ntfy** push messages independent of GitHub's issue notification settings.

1. Install [ntfy for Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy).
2. Create a **random, hard-to-guess topic** (16–64 letters/numbers/underscores/hyphens) and subscribe to it in the app. Do not post the topic publicly; ntfy.sh topics are public to anyone who knows the name.
3. Open repository **Settings → Secrets and variables → Actions → New repository secret**. Name it `NTFY_TOPIC`; set the **value** to exactly the topic name (not the full URL). Do not put the topic in issues, commits, or chats.
4. Open [GitHub Actions workflow](https://github.com/harjotsingh5281/gpt-test/actions/workflows/tcf-monitor.yml) and choose **Run workflow**. Check `notification_test` = **true**. This sends **one test push** via GitHub Actions without visiting the GBLC website or modifying state. It requires the topic secret.
5. Confirm the phone receives the push. Allow ntfy Android notifications and consider battery unrestricted for reliability. Keep GitHub issue alerts as an audit trail.

Slot notifications use ntfy **urgent** priority, link directly to GBLC and include date, time and last observed seat count. Failure alerts use **high** priority after three consecutive failed scans. No notification is sent after an unchanged successful scan.

This is not a private messaging service: on ntfy.sh, topics are public even if obscured by a hard-to-guess name. Only public exam session data is sent; do not send credentials or identity documents. No notification provider guarantees delivery.

## Run the safe manual test

Open **Actions → TCF Canada GBLC slot monitor → Run workflow**. Leave **dry_run** checked. This reads only the public calendar, prints the eligible-session count in logs, and does **not** change state or send alerts.

## After successful booking

Disable the workflow via **Actions → TCF Canada GBLC slot monitor → ... → Disable workflow** to stop scheduled checks. Checks automatically avoid contacting GBLC after December 31, 2026 in Toronto time, although you must disable the workflow to avoid continued GitHub runs.

## Detection and safety

- Parse date from the **exam session** card, never from expected-result dates or registration deadlines.
- Accept only December 10–31, 2026; verify Toronto, Computer, `Select` button, positive seats, corroborating date button, and unexpired registration deadline.
- Preserve last successful state if a scan fails; alert only on previously unseen/reappearing eligible sessions, rather than every unchanged check.
- Treat CAPTCHA, access denial, or unexpected page redesign as failure, not no availability. No CAPTCHA bypass, account automation, or payment automation.
- Browser-install action warnings about Node.js 20 do not affect the current functionality; runner compatibility was fixed by pinning `ubuntu-24.04`.
