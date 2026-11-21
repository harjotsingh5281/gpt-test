# Independent TCF Canada scheduler — Google Apps Script

**Purpose:** Send GitHub `workflow_dispatch` requests from Google's time-driven infrastructure, independently of GitHub's unreliable native `schedule` events. This keeps the existing GitHub Playwright browser scanner, GitHub Issue state, and confirmed GitHub-to-Gmail slot alerts unchanged. This is NOT a new exam scraper.

## Frequencies

| Check | External Google trigger | Existing GitHub internal schedule |
|---|---|---|
| TCF Canada Dec 10–31, 2026 | **1-minute wakeup; sends at most once every 3 minutes** | Kept as secondary fallback |
| TCF Canada Jan 1–31, 2027 | Every **30 minutes** | Kept as secondary fallback |

Google triggers run approximately at the interval; December uses a persistent 3-minute guard to skip wakeups that occur too soon after the last accepted dispatch. It may sometimes run later than 3 minutes; precise wall-clock times are not guaranteed. GitHub may also queue or fail dispatched jobs. Keep the existing ChatGPT hourly health watch enabled.

## SETUP REQUIRED — NOT ACTIVE until you complete these steps

**1. Create a private Google Apps Script project.** Visit https://script.google.com/home/projects/create under your own Gmail account. Name it `TCF Monitor Scheduler`. Replace the default `Code.gs` content with the full code in [Code.gs](Code.gs). **Do not deploy as a web app;** it needs only the two installable time triggers.

**2. Create a narrowly scoped GitHub token.** Visit https://github.com/settings/personal-access-tokens/new . Create a **fine-grained Personal Access Token**, with resource owner `harjotsingh5281`, access to **only** repository `gpt-test`, repository permission **Actions: Read and write** (Metadata: Read is added automatically). Choose an expiration later than **January 31, 2027**, preferably 90 days if creating it in November 2026. Copy the token only into your private Google Apps Script project. **Never post the token in ChatGPT, Gmail, GitHub issues, the public repo, screenshots or code.**

**3. Save the token as a Script Property (not in source code).** In Apps Script choose **Project Settings** (gear) → **Script Properties** → **Add script property**. Name: `GITHUB_PAT`; Value: the fine-grained token. Save.

**4. Authorize and install triggers.** In the Apps Script editor select `installTcfTriggers` from the function selector and click **Run**. Approve Google's authorization screens for time triggers and external HTTP requests. The code deletes only its own two old TCF triggers before re-creating them; re-running setup will not multiply checkers.

**5. Test immediately.** Select `testBothTcfNow` and click **Run**. Open https://github.com/harjotsingh5281/gpt-test/actions and verify TWO **workflow_dispatch** runs, one for each monitor, that complete successfully. These are genuine read-only scans; no fake exam issue will be created. The code sets `dry_run=false` (the GitHub form's default is true), so any actually new session generates a normal GitHub Issue and Gmail notification. The HTTP 204 response in Google logs proves GitHub accepted the dispatch request; only GitHub Actions logs prove the scan completed.

**6. Confirm unattended execution.** In Apps Script sidebar open **Triggers** (clock icon) to see the December every-1-minute wakeup and January every-30-minute triggers, and **Executions** to check their last actual runs. In GitHub Actions the externally triggered runs show **workflow_dispatch**, not **schedule**. They should keep appearing without the laptop running. Run `checkTcfSchedulerStatus` to see installation and last accepted dispatch timestamps.

**7. Stop if you book or no longer need checks.** Run `uninstallTcfTriggers` in Apps Script, and disable the relevant native GitHub workflow and hourly health watch. The script itself skips dispatches after each target month's last day (Toronto local time). The script triggers may continue waking after that until removed, but will not send GitHub requests.

## Troubleshooting / security

- HTTP 204: request accepted, **not** scan success.
- HTTP 401/403: check token validity, expiration, resource owner, correct repository selection, and Actions read/write permission.
- HTTP 404/422: verify the workflow is enabled and the `main` branch has `.github/workflows/tcf-monitor.yml` and `.github/workflows/tcf-january.yml`, with `workflow_dispatch` enabled.
- Google authorization errors: sign into your intended Google account, approve external requests/trigger creation, then run `testBothTcfNow`.
- GitHub email issues currently reach Gmail. The external scheduler never sends any emails directly and cannot bypass GitHub Actions or Google service outages.
- The Google Apps Script project contains a secret Script Property. Keep the project **private**, restrict who can edit it, never publish it as a library or web app, and revoke the GitHub token when monitoring is complete. The GitHub repo contains only public source code, no credentials.
- All tools remain read-only toward GBLC: no login, account access, reservation or payment.
- GitHub's own cron may later recover. In that case both schedulers can launch checks; the workflow has concurrency controls and a persisted session-key state to reduce duplicate alerts, but overlapping schedulers add runner work. After external delivery is verified, you may decide to remove the native `schedule` section to avoid duplicate runs.

## Current status

The user's existing live Google Apps Script installation was verified with December 5-minute and January 30-minute automatic scans. **The new December 3-minute setting is source-only until Code.gs is replaced in the existing private Apps Script project and `installTcfTriggers()` is run again.** Existing `GITHUB_PAT` Script Property is preserved. After updating, verify automatic `workflow_dispatch` runs at approximately 3-minute intervals.

Official references:

- Google supported time intervals: https://developers.google.com/apps-script/reference/script/clock-trigger-builder
- GitHub workflow dispatch REST API: https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event
- Google Apps Script HTTP fetch: https://developers.google.com/apps-script/reference/url-fetch/url-fetch-app
