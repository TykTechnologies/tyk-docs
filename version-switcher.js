console.log('Version hijack script loading...');

// ===== CONFIGURATION =====
// Change this prefix for testing vs production
const PATH_PREFIX = '/mintdocs';  // Change to '/docs' when ready for production

function hijackVersionDropdown() {
    // Version mapping from docs.json
    const versionConfig = {
        '5.8': 'https://tyk.mintlify.app/docs',
        '5.6': 'https://tyk.io/docs/5.6', 
        '5.5': 'https://tyk.io/docs/5.5'
    };
    
    // Target the specific Radix UI dropdown structure
    const versionItems = document.querySelectorAll('div[role="menuitem"][data-radix-collection-item]');
    
    console.log('Found version items:', versionItems.length);
    
    versionItems.forEach(item => {
        const text = item.textContent.trim();
        console.log('Checking item with text:', text);
        
        // Check if this is one of the versions we want to hijack
        if (versionConfig[text]) {
            if (!item.hasAttribute('data-hijacked')) {
                item.setAttribute('data-hijacked', 'true');
                
                // Add click event listener
                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    
                    let currentPath = window.location.pathname;
                    
                    // Remove PATH_PREFIX (with or without version number/name)
                    if (currentPath.startsWith(PATH_PREFIX + '/')) {
                        // Handle /test-docs/X.Y/..., /test-docs/nightly/..., or /test-docs/...
                        const afterPrefix = currentPath.substring((PATH_PREFIX + '/').length);
                        
                        // Check if it starts with a version pattern (X.Y/ or nightly/ or any-word/)
                        const parts = afterPrefix.split('/');
                        const firstPart = parts[0];
                        
                        // Check if first part looks like a version (X.Y format) or special names
                        const isVersion = /^\d+\.\d+$/.test(firstPart) || 
                                         ['nightly', 'latest', 'main', 'dev'].includes(firstPart);
                        
                        if (isVersion && parts.length > 1) {
                            // Remove the version part: /test-docs/5.7/page → /page
                            currentPath = '/' + parts.slice(1).join('/');
                        } else if (isVersion && parts.length === 1) {
                            // Just the version: /test-docs/5.7 → /
                            currentPath = '/';
                        } else {
                            // No version, just /test-docs/page → /page
                            currentPath = '/' + afterPrefix;
                        }
                    } else if (currentPath === PATH_PREFIX) {
                        // Exact match for /test-docs
                        currentPath = '/';
                    }
                    
                    // Ensure we always have a leading slash
                    if (!currentPath.startsWith('/')) {
                        currentPath = '/' + currentPath;
                    }
                    
                    const configuredHref = versionConfig[text];
                    const targetUrl = configuredHref + currentPath;
                    
                    console.log('VERSION HIJACKED!', text, 'Current path:', window.location.pathname, 'Processed path:', currentPath, 'Target URL:', targetUrl);
                    
                    // Close the dropdown before navigating
                    const dropdown = document.querySelector('[data-radix-menu-content]');
                    if (dropdown) {
                        // Method 1: Click outside to close
                        document.body.click();
                        
                        // Method 2: Send Escape key
                        const escEvent = new KeyboardEvent('keydown', {
                            key: 'Escape',
                            code: 'Escape',
                            keyCode: 27,
                            bubbles: true
                        });
                        document.dispatchEvent(escEvent);
                        
                        // Method 3: Try to remove the dropdown manually
                        const popperWrapper = dropdown.closest('[data-radix-popper-content-wrapper]');
                        if (popperWrapper) {
                            popperWrapper.style.display = 'none';
                        }
                    }
                    
                    // Small delay to allow dropdown to close, then navigate
                    setTimeout(function() {
                        window.location.href = targetUrl;
                    }, 150);
                    
                    return false;
                }, true);
                
                console.log('Successfully hijacked version:', text);
            }
        }
    });
}

// Run when dropdown appears (use MutationObserver to detect when it's added to DOM)
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.addedNodes.length) {
            // Check if any added node contains the version dropdown
            mutation.addedNodes.forEach(node => {
                if (node.nodeType === 1) { // Element node
                    // Check if this node or its children contain the dropdown
                    if (node.querySelector && node.querySelector('div[role="menuitem"][data-radix-collection-item]')) {
                        console.log('Version dropdown detected, hijacking...');
                        setTimeout(hijackVersionDropdown, 100); // Small delay to ensure it's fully rendered
                    }
                }
            });
        }
    });
});

// Start observing
observer.observe(document.body, {
    childList: true,
    subtree: true
});

// Also run on page load in case dropdown is already present
setTimeout(hijackVersionDropdown, 1000);
setTimeout(hijackVersionDropdown, 3000);

console.log('Version hijack script loaded and observing!');
