(function () {
  // Matches a version segment such as /5.10/ or /5.10.2/ anywhere in the path.
  // "nightly" is intentionally excluded - it isn't a numbered release users need
  // redirecting away from.
  var versionRegex = /\/\d+\.\d+(\.\d+)?(?=\/|$)/;

  function updateBanner() {
    var banner = document.getElementById('banner');
    if (!banner) return; // user already dismissed this banner, or none rendered

    var onOldVersion = versionRegex.test(location.pathname);

    if (!onOldVersion) {
      // Latest (or nightly) page - this banner is not relevant, hide it.
      // Also clear the height Mintlify reserves for it so no gap is left behind.
      banner.style.display = 'none';
      document.documentElement.style.setProperty('--banner-height', '0px');
      document.documentElement.setAttribute('data-banner-state', 'hidden');
      return;
    }

    banner.style.display = '';
    document.documentElement.setAttribute('data-banner-state', 'visible');

    var link = banner.querySelector('a');
    if (link) {
      link.href = 'https://tyk.io' + location.pathname.replace(versionRegex, '');
    }
  }

  updateBanner();
  // Mintlify is a SPA - re-run as the visitor navigates between pages/versions.
  setInterval(updateBanner, 500);
})();
