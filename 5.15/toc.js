// This script enhances the Table of Contents (TOC) / right side navigation of Mintliffy by adding collapsible/expandable sections based on header depth.
// It also fixes issues with incorrect depth values for custom anchor tags and ensures proper indentation and visibility of TOC items.
// But custom anchor tags are not used anymore in our repository. So that part is not needed anymore.

// toc-fix-v2.js
(function () {
    let observer;
    let activeObserver;

    // Scroll the TOC panel (not the page) so the deepest visible active item is in view.
    // Mintlify highlights the active heading but doesn't scroll the TOC to it, e.g. when a page opens on a #hash.
    function scrollActiveIntoView(toc) {
        const viewport = toc.closest('[data-component-part="scroll-area-viewport"]');
        if (!viewport) return;

        const active = Array.from(toc.querySelectorAll('.toc-item[data-active]'))
            .map(li => li.querySelector(':scope > a'))
            .filter(a => a && a.offsetParent !== null);
        const target = active[active.length - 1];
        if (!target) return;

        const vp = viewport.getBoundingClientRect();
        const rect = target.getBoundingClientRect();
        if (rect.top >= vp.top && rect.bottom <= vp.bottom) return;

        viewport.scrollTo({ top: viewport.scrollTop + rect.top - vp.top - vp.height / 3, behavior: 'smooth' });
    }

    function watchActive(toc) {
        if (activeObserver) activeObserver.disconnect();
        let pending = false;
        activeObserver = new MutationObserver(() => {
            if (pending) return;
            pending = true;
            requestAnimationFrame(() => {
                pending = false;
                scrollActiveIntoView(toc);
            });
        });
        activeObserver.observe(toc, { subtree: true, attributes: true, attributeFilter: ['data-active'] });
        scrollActiveIntoView(toc);
    }

    function run() {
        const toc = document.getElementById('table-of-contents-content');
        if (!toc || toc.dataset.enhanced === 'true') {
            return;
        }
        toc.dataset.enhanced = 'true';

        // Disconnect the observer while we modify the DOM to prevent infinite loops
        if (observer) observer.disconnect();

        const items = Array.from(toc.querySelectorAll('.toc-item'));

        // Normalize depths, fix NaN, and set initial styles
        items.forEach(li => {
            let depthNum = Number(li.getAttribute('data-depth'));
            if (!Number.isFinite(depthNum)) {
                depthNum = 2; // Fix for h4 headers producing NaN
            }
            li.dataset.depth = String(depthNum);
            li.style.display = 'list-item'; // Ensure all items are visible initially
            // Indentation is handled by Mintlify's TOC styles (padding per data-depth)
        });

        // Add toggle buttons and functionality
        items.forEach((li, idx) => {
            const depth = Number(li.dataset.depth);

            // Detect if this item has children
            const hasChild = idx + 1 < items.length && Number(items[idx + 1].dataset.depth) > depth;
            if (!hasChild) return;

            // Prevent adding duplicate toggles if script re-runs
            if (li.querySelector('.toc-toggle')) return;

            const toggle = document.createElement('button');
            toggle.type = 'button';
            toggle.className = 'toc-toggle';
            toggle.setAttribute('aria-expanded', 'true');
            toggle.innerHTML = `
                <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true" focusable="false">
                  <path d="M8.5 10.5 L12 14 L15.5 10.5" stroke="currentColor" stroke-width="1.6" fill="none"
                        stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              `;

            // Keep the anchor as a direct child of the li so Mintlify's `li > a` styles still apply
            const anchor = li.querySelector(':scope > a');
            if (anchor) {
                anchor.after(toggle);
            } else {
                li.appendChild(toggle);
            }

            li.dataset.collapsed = 'false';

            toggle.addEventListener('click', e => {
                e.preventDefault();
                const isCollapsed = li.dataset.collapsed === 'true';
                
                // Toggle the state
                li.dataset.collapsed = String(!isCollapsed);
                toggle.setAttribute('aria-expanded', String(!isCollapsed));
                toggle.classList.toggle('rotated', !isCollapsed);

                // Update visibility of all descendant items
                for (let k = idx + 1; k < items.length; k++) {
                    const childItem = items[k];
                    const childDepth = Number(childItem.dataset.depth);

                    if (childDepth <= depth) {
                        break; // Exited the subtree of the clicked item
                    }

                    if (!isCollapsed) {
                        // If we are COLLAPSING, hide all descendants
                        childItem.style.display = 'none';
                    } else {
                        // If we are EXPANDING, only reveal direct children
                        // Deeper children remain hidden if their own parent is collapsed
                        if (childDepth === depth + 1) {
                            childItem.style.display = 'list-item';
                        }
                    }
                }
            });
        });

        watchActive(toc);

        // Reconnect the observer after DOM modifications are complete
        if (observer) {
            observer.observe(document.body, { childList: true, subtree: true });
        }
    }

    function init() {
        run(); // Run on initial load

        // Set up an observer to re-run the script on SPA navigation
        observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                if (mutation.addedNodes.length > 0) {
                    const toc = document.getElementById('table-of-contents-content');
                    // If a TOC exists and it hasn't been enhanced yet, run the script
                    if (toc && !toc.dataset.enhanced) {
                        run();
                        break; // Found and processed a new TOC, no need to check other mutations
                    }
                }
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
