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
  var SPACER_ID = 'tyk-outdated-banner-spacer';
  var DISMISS_KEY_PREFIX = 'tykBannerDismissed:';
  var HEIGHT_VAR = '--tyk-outdated-banner-height';
  // A dismissal also expires after a fixed number of days, on top of being
  // keyed to LATEST_VERSION below - otherwise someone who dismisses right
  // after a release ships would not see the banner again until the *next*
  // release, however long that takes.
  var DISMISS_DAYS = 7;
  var DISMISS_MS = DISMISS_DAYS * 24 * 60 * 60 * 1000;

  // The two string literals below are substituted at deploy time by
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

  function setDismissed(kind) {
    try {
      localStorage.setItem(
        dismissKey(kind),
        JSON.stringify({ version: LATEST_VERSION, dismissedAt: Date.now() })
      );
    } catch (e) {}
  }

  function isDismissed(kind) {
    try {
      var record = JSON.parse(localStorage.getItem(dismissKey(kind)));
      return (
        !!record &&
        record.version === LATEST_VERSION &&
        Date.now() - record.dismissedAt < DISMISS_MS
      );
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

  function findNavbar() {
    return document.getElementById('navbar');
  }

  // The banner is fixed to the viewport top rather than inserted into the
  // page content, so it stays visible on every scroll position - including
  // landing on an anchor link straight into the middle of a page, which used
  // to scroll straight past a banner embedded at the top of the content.
  function buildBanner(kind) {
    var config = BANNER_CONFIG[kind];

    var el = document.createElement('div');
    el.id = BANNER_ID;
    el.setAttribute('data-kind', kind);
    el.style.cssText =
      'position:fixed;top:0;left:0;width:100%;z-index:45;background:' +
      config.color +
      ';color:#fff;text-align:center;' +
      'font-size:14px;line-height:1.5;padding:10px 44px;box-sizing:border-box;';

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
      setDismissed(kind);
      removeBanner();
    };
    el.appendChild(close);

    return el;
  }

  // An invisible spacer, sized to match the fixed banner's own height, is
  // inserted as the first child of the navbar. The banner is removed from
  // normal flow (position:fixed), so without this the navbar and sidebar
  // would render underneath it; the spacer pushes them down by exactly the
  // banner's height instead, mirroring how Mintlify offsets its own layout
  // for its native (docs.json-configured) banner feature.
  function buildSpacer() {
    var spacer = document.createElement('div');
    spacer.id = SPACER_ID;
    spacer.setAttribute('aria-hidden', 'true');
    spacer.style.cssText = 'width:100%;height:var(' + HEIGHT_VAR + ',0px);';
    return spacer;
  }

  function syncHeight(banner) {
    var height = banner ? banner.offsetHeight : 0;
    document.documentElement.style.setProperty(HEIGHT_VAR, height + 'px');
  }

  function removeBanner() {
    var existing = document.getElementById(BANNER_ID);
    var spacer = document.getElementById(SPACER_ID);
    if (existing) existing.remove();
    if (spacer) spacer.remove();
    document.documentElement.style.removeProperty(HEIGHT_VAR);
  }

  function updateBanner() {
    var existing = document.getElementById(BANNER_ID);
    var kind = bannerKind();

    if (!kind || isDismissed(kind)) {
      if (existing) removeBanner();
      return;
    }

    if (existing && existing.getAttribute('data-kind') !== kind) {
      removeBanner();
      existing = null;
    }

    var navbar = findNavbar();

    if (!existing) {
      existing = buildBanner(kind);
      if (navbar && navbar.parentNode) {
        navbar.parentNode.insertBefore(existing, navbar);
      } else {
        document.body.insertBefore(existing, document.body.firstChild);
      }
      syncHeight(existing);
    }

    // The spacer lives inside the navbar's own subtree, so it can be dropped
    // by a navbar re-render independently of the banner itself surviving -
    // re-check and reinsert it on every update, not just when first built.
    if (navbar && !document.getElementById(SPACER_ID)) {
      navbar.insertBefore(buildSpacer(), navbar.firstChild);
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

  // The banner's height changes with viewport width (its text wraps onto
  // more lines on narrow screens), so the spacer/layout offset needs to be
  // recalculated whenever the window resizes, not just once on load.
  var scheduleResync = debounce(function () {
    syncHeight(document.getElementById(BANNER_ID));
  }, 100);
  window.addEventListener('resize', scheduleResync);

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

  // Observed at the body level (not just the navbar) because the spacer
  // lives inside the navbar's own React-managed subtree - a re-render there
  // could drop it even when the navbar element itself is untouched.
  new MutationObserver(scheduleUpdate).observe(document.body, {
    childList: true,
    subtree: true,
  });
})();
