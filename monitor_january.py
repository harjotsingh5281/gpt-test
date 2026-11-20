"""Read-only GBLC TCF Canada availability monitor (Toronto, January 2027)."""
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from datetime import date, datetime
from zoneinfo import ZoneInfo

URL = "https://gblc.ca/en/book-now/choose-date?test=6"
START, END = date(2027, 1, 1), date(2027, 1, 31)
MONTHS = {v.lower(): k for k, v in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
CARD = re.compile(r"\bTCF Canada(?:\s+Group Test Time)?\s+(?P<seats>\d+)\s+Group Test Time\s+(?:MON|TUE|WED|THU|FRI|SAT|SUN)\s+(?P<day>\d{1,2})\s+(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(?P<year>20\d{2})\b", re.I)
PILL = re.compile(r"^\s*(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(?P<day>\d{1,2})\s+(?:MON|TUE|WED|THU|FRI|SAT|SUN)\s+(?P<seats>\d+)\s+Slots?\s*$", re.I)
TIME = re.compile(r"\b\d{1,2}:\d{2}\s*(?:AM|PM)\b", re.I)
DEADLINE = re.compile(r"Registration Deadline:\s+(?:MON|TUE|WED|THU|FRI|SAT|SUN)\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(20\d{2})", re.I)
STATE_TITLE = "[TCF January Monitor] Internal state (do not close)"
MARKER = "TCF_MONITOR_JAN2027_STATE_V1:"

class CheckError(RuntimeError):
    pass

def parse(body, buttons, today):
    if not re.search(r"TCF Canada\s*-\s*Computer", body, re.I):
        raise CheckError("TCF Canada - Computer selection was not verified")
    cards = list(CARD.finditer(body))
    if not cards:
        raise CheckError("No recognizable GBLC examination cards; site may be blocked or redesigned")
    counts = {}
    for text in buttons:
        m = PILL.fullmatch(" ".join(text.split()))
        if m:
            key = (MONTHS[m["month"].lower()], int(m["day"]))
            counts[key] = max(counts.get(key, 0), int(m["seats"]))
    matches = {}
    for i, m in enumerate(cards):
        exam_date = date(int(m["year"]), MONTHS[m["month"].lower()], int(m["day"]))
        if exam_date < today or not START <= exam_date <= END or int(m["seats"]) < 1:
            continue
        segment = body[m.end() : cards[i+1].start() if i+1 < len(cards) else len(body)]
        if not (re.search(r"(?m)^\s*Select\s*$", segment, re.I) and
                re.search(r"\bToronto\b", segment, re.I) and re.search(r"\bComputer\b", segment, re.I)):
            continue
        dl = DEADLINE.search(segment)
        if dl and date(int(dl[3]), MONTHS[dl[2].lower()], int(dl[1])) < today:
            continue
        if counts.get((exam_date.month, exam_date.day), 0) < 1:
            raise CheckError(f"{exam_date}: session card present but no matching positive-Slots button")
        first = segment.split("Expected Result Date:", 1)[0]
        start = TIME.search(first)
        if not start:
            raise CheckError(f"{exam_date}: no group-exam start time found")
        group_start = " ".join(start.group().upper().split())
        key = f"{exam_date}|{group_start}"
        matches[key] = {"date": str(exam_date), "time": group_start, "seats": int(m["seats"])}
    return matches, len(cards)

def scan():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="en-CA", timezone_id="America/Toronto")
        page = context.new_page()
        try:
            response = page.goto(URL, wait_until="domcontentloaded", timeout=35000)
            if not response or response.status >= 400:
                raise CheckError(f"GBLC HTTP status {response.status if response else 'unknown'}")
            try:
                page.wait_for_function("() => document.body.innerText.includes('Group Test Time')", timeout=25000)
            except Exception as exc:
                raise CheckError("GBLC examination cards did not load in time") from exc
            body = page.locator("body").inner_text()
            buttons = page.locator("button").all_inner_texts()
            try:
                return parse(body, buttons, datetime.now(ZoneInfo("America/Toronto")).date())
            except CheckError:
                if os.environ.get("DRY_RUN") == "1":
                    # Public booking-page text only. Never dump cookies or private form values.
                    position = body.find("Group Test Time")
                    print("DIAGNOSTIC: page title:", page.title(), flush=True)
                    print("DIAGNOSTIC: text around first group time:", repr(body[max(0, position-300):position+1700]), flush=True)
                    print("DIAGNOSTIC: date buttons:", repr([b for b in buttons if "Slots" in b][:8]), flush=True)
                raise
        except Exception:
            try:
                page.screenshot(path="gblc-error.png")
            except Exception:
                pass
            raise
        finally:
            context.close()
            browser.close()

def api(method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
               "Accept": "application/vnd.github+json", "User-Agent": "gblc-readonly-monitor",
               "X-GitHub-Api-Version": "2022-11-28"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request("https://api.github.com/repos/" + os.environ["GITHUB_REPOSITORY"] + path,
                                     data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)

def create_issue(title, body):
    owner = os.environ["GITHUB_REPOSITORY"].split("/")[0]
    return api("POST", "/issues", {"title": title, "body": body, "assignees": [owner]})["html_url"]

def state_get():
    issues = api("GET", "/issues?state=all&per_page=100")
    issue = next((x for x in issues if x.get("title") == STATE_TITLE and "pull_request" not in x), None)
    if not issue:
        return None, {"keys": [], "failures": 0, "reported": False}
    m = re.search(re.escape(MARKER) + r"([^\n]+)", issue.get("body") or "")
    if not m:
        raise CheckError("Monitoring state issue has invalid format")
    return issue["number"], json.loads(m[1])

def state_save(issue_num, state):
    body = "Read-only TCF Canada monitoring state. Please do not edit.\n\n" + MARKER + json.dumps(state, sort_keys=True)
    if issue_num:
        api("PATCH", f"/issues/{issue_num}", {"body": body})
    else:
        api("POST", "/issues", {"title": STATE_TITLE, "body": body})

def discord(message):
    url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not url:
        return
    if not re.fullmatch(r"https://(?:discord\.com|discordapp\.com)/api/webhooks/[^/\s]+/[^/\s]+", url):
        raise CheckError("Invalid Discord webhook URL")
    req = urllib.request.Request(url, data=json.dumps({"content": message[:1900]}).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "gblc-readonly-monitor"})
    with urllib.request.urlopen(req, timeout=15):
        pass

def ntfy_notify(message, title="TCF January monitor", priority="high", url=URL):
    """Push to an ntfy.sh topic stored only as a GitHub Actions secret."""
    topic = (os.environ.get("NTFY_TOPIC_JANUARY") or os.environ.get("NTFY_TOPIC", "")).strip()
    if not topic:
        return False
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", topic):
        raise CheckError("NTFY_TOPIC must have 16-64 letters, numbers, hyphens or underscores")
    headers = {"Title": title[:90], "Priority": priority, "Click": url,
               "Content-Type": "text/plain; charset=utf-8", "User-Agent": "gblc-readonly-monitor"}
    request = urllib.request.Request("https://ntfy.sh/" + topic, data=message.encode("utf-8"),
                                     headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status not in (200, 201):
            raise CheckError(f"ntfy returned HTTP {response.status}")
    return True


def main():
    if os.environ.get("NOTIFICATION_TEST") == "1":
        if not (os.environ.get("NTFY_TOPIC_JANUARY") or os.environ.get("NTFY_TOPIC", "")).strip():
            raise CheckError("Set GitHub Actions secret NTFY_TOPIC_JANUARY (or NTFY_TOPIC) before notification_test")
        ntfy_notify("TEST ONLY: GitHub Actions sent this message. No exam slot has been found.",
                    title="TCF JANUARY - TEST ONLY", priority="high", url=URL)
        print("NTFY TEST: notification successfully accepted by ntfy.sh")
        return 0
    today = datetime.now(ZoneInfo("America/Toronto")).date()
    if today > END:
        print("Target date window expired; no network request to GBLC.")
        return 0
    if os.environ.get("DRY_RUN") == "1":
        slots, card_count = scan()
        print(f"DRY RUN: {card_count} examination cards; {len(slots)} eligible sessions: {json.dumps(slots)}")
        return 0
    number, state = state_get()
    try:
        slots, card_count = scan()
    except Exception as exc:
        state["failures"] = state.get("failures", 0) + 1
        if state["failures"] >= 3 and not state.get("reported"):
            link = create_issue("[TCF JANUARY] Three consecutive failed checks",
                                f"Could not verify the public GBLC calendar; previous availability state retained.\n\nLast error: {str(exc)[:500]}")
            state["reported"] = True
            try:
                discord("⚠️ GBLC January calendar monitoring has failed 3 times: " + link)
            except Exception as notify_error:
                print("Discord notification failed:", notify_error, file=sys.stderr)
            try:
                ntfy_notify("GBLC January calendar monitoring has failed 3 consecutive times. Check workflow logs: " + link,
                            title="TCF JANUARY - CHECK FAILED", priority="high", url=link)
            except Exception as notify_error:
                print("ntfy failure notification failed:", notify_error, file=sys.stderr)
        state_save(number, state)
        raise
    old = set(state.get("keys", []))
    current = set(slots)
    new = sorted(current - old)
    if new:
        details = "\n".join(f"- {slots[k]['date']} {slots[k]['time']}: {slots[k]['seats']} observed seats" for k in new)
        issue = create_issue("[TCF JAN SLOT] " + ", ".join(sorted({slots[k]["date"] for k in new})),
            f"**New eligible TCF Canada – Computer sessions in Toronto:**\n\n{details}\n\nBook manually: {URL}\n\nAvailability may change. No seat has been reserved.")
        print("SLOT ALERT:", issue)
        try:
            discord("🚨 GBLC January 2027 TCF Canada slot found:\n" + details + "\n" + URL + "\n" + issue)
        except Exception as notify_error:
            print("Discord notification failed; GitHub issue still exists:", notify_error, file=sys.stderr)
        try:
            ntfy_notify("New January 2027 GBLC TCF Canada session(s):\n" + details + "\nBook manually: " + URL,
                        title="TCF JANUARY - BOOKABLE SLOT FOUND", priority="urgent", url=URL)
        except Exception as notify_error:
            print("ntfy slot notification failed; GitHub issue still exists:", notify_error, file=sys.stderr)
    else:
        print(f"OK: {card_count} exam cards inspected; no new eligible session.")
    had_failures = bool(state.get("failures") or state.get("reported"))
    state.update(keys=sorted(current), failures=0, reported=False)
    if number is None or current != old or had_failures:
        state_save(number, state)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("Monitor failed:", repr(exc), file=sys.stderr)
        sys.exit(1)
