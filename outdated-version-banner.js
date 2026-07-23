(function () {
  // Merged deploys copy this file into version folders too, and Mintlify
  // includes every .js in the content directory globally - run only once.
  if (window.__tykOutdatedBannerInit) return;
  window.__tykOutdatedBannerInit = true;

  // Matches a version segment such as /5.10/ or /5.10.2/ anywhere in the path.
  // "nightly" is intentionally excluded - it isn't a numbered release users need
  // redirecting away from.
  var versionRegex = /\/(\d+\.\d+(?:\.\d+)?)(?=\/|$)/;

  var BANNER_ID = 'tyk-outdated-banner';
  var DISMISS_KEY_PREFIX = 'tykBannerDismissed:';

  // {{LATEST_VERSION}} and {{LTS_VERSIONS}} are substituted at deploy time by
  // scripts/merge_docs_configs.py: LATEST_VERSION from whichever version
  // branches-config.json marks isLatest, LTS_VERSIONS as a JSON array of every
  // target_folder marked isLts. Dismissal is keyed to LATEST_VERSION, so both
  // banners automatically reappear for everyone once a new version ships.
  var LATEST_VERSION = '{{LATEST_VERSION}}';
  var LTS_VERSIONS = (function () {
    try {
      return JSON.parse('{{LTS_VERSIONS}}');
    } catch (e) {
      return [];
    }
  })();

  var BANNER_CONFIG = {
    outdated: {
      color: '#d97706',
      icon: '⚠️ ',
      title: 'Outdated Version',
      body:
        ' - This page refers to an older version of our documentation. ' +
        'We recommend using the ',
      linkText: 'latest release (v' + LATEST_VERSION + ')',
      suffix: ' for the most up-to-date guidance.',
    },
    lts: {
      color: '#2563eb',
      icon: 'ℹ️ ',
      title: 'Long Term Support (LTS) Version',
      body: " - If you'd like to see what's new, the ",
      linkText: 'latest release (v' + LATEST_VERSION + ')',
      suffix: ' is available here.',
    },
  };

  function dismissKey(kind) {
    return DISMISS_KEY_PREFIX + kind;
  }

  function isDismissed(kind) {
    try {
      return localStorage.getItem(dismissKey(kind)) === LATEST_VERSION;
    } catch (e) {
      return false;
    }
  }

  function pathVersion() {
    var match = versionRegex.exec(location.pathname);
    return match ? match[1] : null;
  }

  function bannerKind() {
    var version = pathVersion();
    if (!version) return null;
    return LTS_VERSIONS.indexOf(version) !== -1 ? 'lts' : 'outdated';
  }

  function buildBanner(kind) {
    var config = BANNER_CONFIG[kind];

    var el = document.createElement('div');
    el.id = BANNER_ID;
    el.setAttribute('data-kind', kind);
    el.style.cssText =
      'position:relative;background:' +
      config.color +
      ';color:#fff;text-align:center;' +
      'font-size:14px;line-height:1.5;padding:10px 44px;border-radius:8px;' +
      'margin:0 0 20px 0;';

    var text = document.createElement('span');
    text.appendChild(document.createTextNode(config.icon));

    var strong = document.createElement('strong');
    strong.textContent = config.title;
    text.appendChild(strong);

    text.appendChild(document.createTextNode(config.body));

    var link = document.createElement('a');
    link.setAttribute('data-role', 'latest-link');
    link.style.cssText = 'color:#fff;font-weight:600;text-decoration:underline;';
    link.textContent = config.linkText;
    text.appendChild(link);

    text.appendChild(document.createTextNode(config.suffix));

    el.appendChild(text);

    var close = document.createElement('button');
    close.setAttribute('aria-label', 'Dismiss banner');
    close.textContent = '✕';
    close.style.cssText =
      'position:absolute;right:12px;top:50%;transform:translateY(-50%);' +
      'background:none;border:none;color:#fff;font-size:16px;cursor:pointer;padding:4px;';
    close.onclick = function () {
      try {
        localStorage.setItem(dismissKey(kind), LATEST_VERSION);
      } catch (e) {}
      el.remove();
    };
    el.appendChild(close);

    return el;
  }

  function findContentContainer() {
    return (
      document.getElementById('content-area') ||
      document.getElementById('content-container') ||
      document.querySelector('main')
    );
  }

  function updateBanner() {
    var existing = document.getElementById(BANNER_ID);
    var kind = bannerKind();

    if (!kind || isDismissed(kind)) {
      if (existing) existing.remove();
      return;
    }

    if (existing && existing.getAttribute('data-kind') !== kind) {
      existing.remove();
      existing = null;
    }

    if (!existing) {
      var container = findContentContainer();
      if (!container) return;
      existing = buildBanner(kind);
      try {
        container.insertBefore(existing, container.firstChild);
      } catch (e) {
        return;
      }
    }

    // Point the link at the same page in the latest version (strip the
    // version segment), keeping any query string or anchor so the reader
    // lands on the exact same section, not just the top of the page.
    var link = existing.querySelector('a[data-role="latest-link"]');
    if (link) {
      link.href =
        location.origin +
        location.pathname.replace(versionRegex, '') +
        location.search +
        location.hash;
    }
  }

  function debounce(fn, wait) {
    var timer;
    return function () {
      clearTimeout(timer);
      timer = setTimeout(fn, wait);
    };
  }

  var scheduleUpdate = debounce(updateBanner, 100);

  // Mintlify is a SPA: client-side navigation changes the path via the
  // History API without a full page load. Hook both so we catch it, then
  // fall back to a MutationObserver in case a route swaps content without
  // going through history (e.g. an in-place re-render).
  ['pushState', 'replaceState'].forEach(function (method) {
    var original = history[method];
    history[method] = function () {
      var result = original.apply(this, arguments);
      scheduleUpdate();
      return result;
    };
  });
  window.addEventListener('popstate', scheduleUpdate);

  updateBanner();

  var observeTarget = findContentContainer() || document.body;
  new MutationObserver(scheduleUpdate).observe(observeTarget, {
    childList: true,
    subtree: true,
  });
})();
