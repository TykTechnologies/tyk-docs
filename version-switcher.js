console.log('Version hijack script loading...');

function hijackVersionDropdown() {
    // Version mapping from docs.json
    const versionConfig = {
        '5.8-Latest': 'https://tyk.mintlify.app',
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
                    
                    const currentPath = window.location.pathname;
                    const configuredHref = versionConfig[text];
                    const targetUrl = configuredHref + currentPath;
                    
                    console.log('VERSION HIJACKED!', text, 'Current path:', currentPath, 'Target URL:', targetUrl);
                    
                    // Navigate to the same page in the selected version
                    window.location.href = targetUrl;
                    
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
