/**
 * Independent cloud scheduler for the public GBLC TCF Canada monitors.
 *
 * Safe to store in a public repository: NO access token is hard-coded here.
 * Paste this into a PRIVATE standalone Google Apps Script project.
 * Add GITHUB_PAT as a Script Property in Apps Script project settings.
 *
 * Google triggers: December 1-minute wakeups with a 3-minute dispatch guard, January every 30 minutes.
 * GitHub workflow_dispatch starts the existing, read-only Playwright checkers.
 * Notification delivery remains GitHub Issue -> Gmail.
 */

const TCF_SCHEDULER = Object.freeze({
  repository: 'harjotsingh5281/gpt-test',
  branch: 'main',
  timezone: 'America/Toronto',
  decemberWorkflow: 'tcf-monitor.yml',
  januaryWorkflow: 'tcf-january.yml',
  decemberMinIntervalMs: 3 * 60 * 1000,
  decemberEnd: '2026-12-31',
  januaryEnd: '2027-01-31'
});

/**
 * Run this ONCE after setting the GITHUB_PAT Script Property.
 * Re-running it replaces ONLY the two TCF triggers (no duplicates).
 */
function installTcfTriggers() {
  requireGitHubToken_();

  const names = ['checkDecemberTcf', 'maybeCheckDecemberTcf', 'checkJanuaryTcf'];
  ScriptApp.getProjectTriggers().forEach(function(trigger) {
    if (names.indexOf(trigger.getHandlerFunction()) !== -1) {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  ScriptApp.newTrigger('maybeCheckDecemberTcf')
    .timeBased().everyMinutes(1).create();

  ScriptApp.newTrigger('checkJanuaryTcf')
    .timeBased().everyMinutes(30).create();

  Logger.log('Installed December 1-minute wakeups (3-minute dispatch guard) and January 30-minute trigger.');
  Logger.log('Next: run testBothTcfNow() and check GitHub Actions for two workflow_dispatch runs.');
}

/** Scheduled December trigger: wake every minute, dispatch no more often than 3 minutes. */
function maybeCheckDecemberTcf() {
  dispatchTcf_(
    TCF_SCHEDULER.decemberWorkflow,
    TCF_SCHEDULER.decemberEnd,
    'December',
    TCF_SCHEDULER.decemberMinIntervalMs
  );
}

/** Manual December scan (no interval guard), used by testBothTcfNow(). */
function checkDecemberTcf() {
  dispatchTcf_(
    TCF_SCHEDULER.decemberWorkflow,
    TCF_SCHEDULER.decemberEnd,
    'December'
  );
}

/** Trigger for the January 1-31, 2027 monitor. */
function checkJanuaryTcf() {
  dispatchTcf_(
    TCF_SCHEDULER.januaryWorkflow,
    TCF_SCHEDULER.januaryEnd,
    'January'
  );
}

/**
 * Manual end-to-end dispatch test. Sends NO fake slot email.
 * It starts both real GitHub monitors and any genuinely new slots
 * are handled by their existing deduplication + alert logic.
 */
function testBothTcfNow() {
  checkDecemberTcf();
  checkJanuaryTcf();
  Logger.log('Both dispatch requests attempted. Confirm the two GitHub runs succeeded.');
}

/**
 * Inspect registered triggers plus the last successful dispatch requests.
 * A successful dispatch is NOT proof that the GitHub scan completed.
 */
function checkTcfSchedulerStatus() {
  const triggers = ScriptApp.getProjectTriggers()
    .map(function(t) { return t.getHandlerFunction(); });
  const props = PropertiesService.getScriptProperties();
  Logger.log('December 3-minute dispatch guard trigger installed: ' + triggers.includes('maybeCheckDecemberTcf'));
  Logger.log('January trigger installed: ' + triggers.includes('checkJanuaryTcf'));
  Logger.log('Last December request accepted: ' +
    (props.getProperty('TCF_DEC_LAST_ACCEPTED_UTC') || 'Never'));
  Logger.log('Last January request accepted: ' +
    (props.getProperty('TCF_JAN_LAST_ACCEPTED_UTC') || 'Never'));
  Logger.log('Confirm scan success in GitHub Actions; these are dispatch-only timestamps.');
}

/** Optional: stop the external scheduler after booking or January 2027. */
function uninstallTcfTriggers() {
  const names = ['checkDecemberTcf', 'maybeCheckDecemberTcf', 'checkJanuaryTcf'];
  ScriptApp.getProjectTriggers().forEach(function(t) {
    if (names.indexOf(t.getHandlerFunction()) !== -1) {
      ScriptApp.deleteTrigger(t);
    }
  });
  Logger.log('TCF external scheduler triggers removed.');
}

function requireGitHubToken_() {
  const token = PropertiesService.getScriptProperties().getProperty('GITHUB_PAT');
  if (!token || token.trim().length < 20) {
    throw new Error('Set the GITHUB_PAT Script Property first. Do NOT paste token in source code or ChatGPT.');
  }
  return token.trim();
}

function dispatchTcf_(workflow, lastDate, label, minIntervalMs) {
  const localToday = Utilities.formatDate(new Date(), TCF_SCHEDULER.timezone, 'yyyy-MM-dd');
  if (localToday > lastDate) {
    Logger.log(label + ' date window ended; skipping dispatch.');
    return;
  }

  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) {
    Logger.log(label + ' dispatch skipped because another dispatch is already running.');
    return;
  }

  try {
    // Script lock makes the timing guard safe even if two minute ticks overlap.
    const props = PropertiesService.getScriptProperties();
    if (minIntervalMs) {
      const lastAcceptedMs = Number(props.getProperty('TCF_DEC_LAST_ACCEPTED_EPOCH_MS') || 0);
      if (lastAcceptedMs && Date.now() - lastAcceptedMs < minIntervalMs) {
        Logger.log(label + ': 3-minute dispatch interval not elapsed; skipping this 1-minute wakeup.');
        return;
      }
    }

    const token = requireGitHubToken_();
    const url = 'https://api.github.com/repos/' + TCF_SCHEDULER.repository +
      '/actions/workflows/' + workflow + '/dispatches';

    // Must explicitly pass dry_run=false: the GitHub manual-run default is TRUE.
    const payload = {
      ref: TCF_SCHEDULER.branch,
      inputs: {
        dry_run: 'false',
        notification_test: 'false'
      }
    };

    const response = UrlFetchApp.fetch(url, {
      method: 'post',
      contentType: 'application/json',
      headers: {
        Authorization: 'Bearer ' + token,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'gblc-tcf-independent-scheduler'
      },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });

    const status = response.getResponseCode();
    if (status !== 204) {
      // Do not print request headers, token or full response body.
      throw new Error(label + ' GitHub dispatch failed (HTTP ' + status +
        '). Check that GITHUB_PAT is valid and has Actions: read/write for gpt-test.');
    }

    const property = label === 'December'
      ? 'TCF_DEC_LAST_ACCEPTED_UTC' : 'TCF_JAN_LAST_ACCEPTED_UTC';
    const accepted = Utilities.formatDate(new Date(), 'UTC', 'yyyy-MM-dd HH:mm:ss');
    props.setProperty(property, accepted);
    if (label === 'December') {
      props.setProperty('TCF_DEC_LAST_ACCEPTED_EPOCH_MS', String(Date.now()));
    }
    Logger.log(label + ' GitHub dispatch ACCEPTED at ' + accepted +
      ' UTC. Check GitHub Actions for the actual scan result.');
  } finally {
    lock.releaseLock();
  }
}
