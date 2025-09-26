// toc-fix-v2.js
(function () {
    let observer;

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

            const a = li.querySelector('a');
            if (a) {
                const indentStep = 1; // rem per depth level
                a.style.marginLeft = `${depthNum * indentStep}rem`;
            }
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

            const anchor = li.querySelector('a');
            if (anchor) {
                const wrapper = document.createElement('div');
                wrapper.className = 'toc-row';
                // Insert wrapper before the anchor, then move anchor and toggle into it
                anchor.parentNode.insertBefore(wrapper, anchor);
                wrapper.appendChild(anchor);
                wrapper.appendChild(toggle);
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
