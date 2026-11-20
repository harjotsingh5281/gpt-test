# GBLC TCF Canada slot monitor

Read-only monitoring for **TCF Canada – Computer** examinations at GB Language Centre, Toronto, between **December 10 and December 31, 2026**.

Booking page: https://gblc.ca/en/book-now/choose-date?test=6

The monitor **never** signs in, uploads passports, reserves dates, or makes payments. It alerts via a GitHub issue assigned to the repository owner, optionally via Discord webhook. An alert means the seat was visible at the time checked, not reserved.

## Testing before recurring checks
The initial workflow runs parser tests on push. In GitHub, open **Actions → TCF Canada GBLC slot monitor → Run workflow** with **dry_run: true** to inspect the live calendar without creating alerts or updating state. Check the results and screenshot artifacts.

Only after successful inspection should the 15-minute schedule be added to the workflow:
```yaml
  schedule:
    - cron: '7,22,37,52 * * * *'
```
Scheduled checks may be delayed or skipped by GitHub; they are not an exact guarantee.

## Notifications
GitHub issues are assigned to the repository owner on new eligible sessions; enable GitHub mobile/email **issue-assignment notifications**. Avoid Actions-success notification spam. Optionally add the Actions secret `DISCORD_WEBHOOK_URL` (never commit its value) to push messages to a Discord channel.

## Safety and monitoring logic
- Check only the official GBLC date-selection page; no booking or payment steps.
- Require a full-year **TCF Canada** session card for Toronto with a `Select` control, positive slot count, and corroborating positive-slot date button.
- Only alert on newly detected session/date keys (including reappearances after a successful no-slot scan).
- Do not reset availability after a scan failure; after 3 consecutive errors create a separate failure issue.
- Stop contacting GBLC after December 31, 2026 (Toronto time).
- Stop if the site blocks the checker; do not bypass CAPTCHA/Queue-Fair.
- A failed GitHub scheduler with no runs needs an independent external heartbeat service to be detectable.
