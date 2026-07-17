(function () {
  // Matches a version segment such as /5.10/ or /5.10.2/ anywhere in the path.
  // "nightly" is intentionally excluded - it isn't a numbered release users need
  // redirecting away from.
  var versionRegex = /\/\d+\.\d+(\.\d+)?(?=\/|$)/;
  var DISMISS_KEY_SUFFIX = 'bannerDismissed'; // matches Mintlify's own dismissal storage key

  // Mirrors Mintlify's own dismissal check: a banner is dismissed if some
  // localStorage key ends in "bannerDismissed" and its stored value matches
  // this banner's exact text.
  function isDismissed(bannerText) {
    for (var i = 0; i < localStorage.length; i++) {
      var key = localStorage.key(i);
      if (key && key.endsWith(DISMISS_KEY_SUFFIX) && localStorage.getItem(key) === bannerText) {
        return true;
      }
    }
    return false;
  }

  function updateBanner() {
    var banner = document.getElementById('banner');
    if (!banner) return;

    var onOldVersion = versionRegex.test(location.pathname);

    if (!onOldVersion) {
      // Latest (or nightly) page - this banner is never relevant here, regardless
      // of whether the visitor has dismissed it elsewhere.
      document.documentElement.setAttribute('data-banner-state', 'hidden');
      return;
    }

    // Old version page - respect the visitor's existing dismissal choice rather
    // than forcing it back open (Mintlify's own dismiss check only runs once on
    // full page load, not on the client-side navigations between versions).
    document.documentElement.setAttribute(
      'data-banner-state',
      isDismissed(banner.innerText) ? 'hidden' : 'visible'
    );

    var link = banner.querySelector('a');
    if (link) {
      link.href = location.origin + location.pathname.replace(versionRegex, '');
    }
  }

  updateBanner();
  // Mintlify is a SPA - re-run as the visitor navigates between pages/versions.
  setInterval(updateBanner, 500);
})();
