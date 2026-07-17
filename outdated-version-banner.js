(function () {
  // Merged deploys copy this file into version folders too, and Mintlify
  // includes every .js in the content directory globally - run only once.
  if (window.__tykOutdatedBannerInit) return;
  window.__tykOutdatedBannerInit = true;

  // Matches a version segment such as /5.10/ or /5.10.2/ anywhere in the path.
  // "nightly" is intentionally excluded - it isn't a numbered release users need
  // redirecting away from.
  var versionRegex = /\/\d+\.\d+(\.\d+)?(?=\/|$)/;

  var BANNER_ID = 'tyk-outdated-banner';
  var DISMISS_KEY = 'tykOutdatedBannerDismissed';

  // {{LATEST_VERSION}} is substituted at deploy time by
  // scripts/merge_docs_configs.py with whichever version branches-config.json
  // marks isLatest (e.g. "5.14"). Because dismissal stores this exact text,
  // the banner automatically reappears for everyone on the next release.
  var MESSAGE =
    '⚠️ <strong>Outdated Version</strong> - This page refers to an ' +
    'older version of our documentation. We recommend using the ' +
    '<a data-role="latest-link" href="/docs" style="color:#fff;font-weight:600;text-decoration:underline;">' +
    'latest release (v{{LATEST_VERSION}})</a> for the most up-to-date guidance.';

  function isDismissed() {
    try {
      return localStorage.getItem(DISMISS_KEY) === MESSAGE;
    } catch (e) {
      return false;
    }
  }

  function buildBanner() {
    var el = document.createElement('div');
    el.id = BANNER_ID;
    el.style.cssText =
      'position:relative;background:#d97706;color:#fff;text-align:center;' +
      'font-size:14px;line-height:1.5;padding:10px 44px;border-radius:8px;' +
      'margin:0 0 20px 0;';

    var text = document.createElement('span');
    text.innerHTML = MESSAGE;
    el.appendChild(text);

    var close = document.createElement('button');
    close.setAttribute('aria-label', 'Dismiss banner');
    close.innerHTML = '✕';
    close.style.cssText =
      'position:absolute;right:12px;top:50%;transform:translateY(-50%);' +
      'background:none;border:none;color:#fff;font-size:16px;cursor:pointer;padding:4px;';
    close.onclick = function () {
      try {
        localStorage.setItem(DISMISS_KEY, MESSAGE);
      } catch (e) {}
      el.remove();
    };
    el.appendChild(close);

    return el;
  }

  function updateBanner() {
    var existing = document.getElementById(BANNER_ID);
    var onOldVersion = versionRegex.test(location.pathname);

    if (!onOldVersion || isDismissed()) {
      if (existing) existing.remove();
      return;
    }

    if (!existing) {
      // Insert at the top of the content column; fall back to wider containers
      // if Mintlify ever renames the inner ones.
      var anchor =
        document.getElementById('content-area') ||
        document.getElementById('content-container') ||
        document.querySelector('main');
      if (!anchor) return;
      existing = buildBanner();
      try {
        anchor.insertBefore(existing, anchor.firstChild);
      } catch (e) {
        return;
      }
    }

    // Point the link at the same page in the latest version (strip the
    // version segment). Re-done every tick since the path changes as the
    // visitor navigates.
    var link = existing.querySelector('a[data-role="latest-link"]');
    if (link) {
      link.href = location.origin + location.pathname.replace(versionRegex, '');
    }
  }

  updateBanner();
  // Mintlify is a SPA: client-side navigation re-renders the content column,
  // which both changes the path and wipes our injected node - re-check and
  // re-insert as the visitor moves around.
  setInterval(updateBanner, 500);
})();
