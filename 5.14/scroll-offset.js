/**
 * Scroll Offset Handler
 * Enforces custom scroll offsets for anchors with data-scroll-offset attribute
 * Runs after page load to override any default scroll behavior
 */

function handleScrollOffset() {
    // Get the current hash from the URL
    const hash = window.location.hash;

    if (!hash) return;

    // Find the anchor element
    const anchorId = hash.substring(1); // Remove the '#'
    const anchor = document.getElementById(anchorId);

    if (!anchor) return;

    console.log(`Found anchor for hash: ${hash}`);

    // Check if the anchor has the data-scroll-offset attribute
    const scrollOffsetAttr = anchor.getAttribute('data-scroll-offset');

    if (scrollOffsetAttr === null) return; // No scroll offset attribute

    console.log(`Applying custom scroll offset for anchor: ${anchorId}`);

    // Calculate the scroll position
    const elementRect = anchor.getBoundingClientRect();
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const offset = 160; // pixels
    const targetScrollPosition = scrollTop + elementRect.top - offset;

    // Scroll to the calculated position
    window.scrollTo({
        top: targetScrollPosition,
        behavior: 'auto' // Use auto to match instant behavior of hash navigation
    });
}

// Run on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', handleScrollOffset);
} else {
    // If DOM is already loaded, run immediately
    handleScrollOffset();
}

// Also handle hash changes
window.addEventListener('hashchange', handleScrollOffset);

// Run a delayed version to catch any late-loading content
setTimeout(handleScrollOffset, 500);
setTimeout(handleScrollOffset, 1500);
