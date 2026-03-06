(function() {
  // Helper function to get meta content
  function getMetaContent(name) {
    const meta = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
    return meta ? meta.getAttribute('content') : '';
  }

  // Helper function to get page summary
  function getPageSummary() {
    const description = getMetaContent('description') || getMetaContent('og:description');
    if (description) return description;
    
    // Fallback: get first paragraph text from content area
    const firstP = document.querySelector('.mdx-content p, #content-area p, [id*="content"] p');
    return firstP ? firstP.textContent.substring(0, 160) + '...' : '';
  }

  // Helper function to extract tags/keywords
  function getKeywords() {
    const keywords = getMetaContent('keywords');
    if (keywords) {
      return keywords.split(',').map(k => k.trim()).filter(k => k);
    }
    
    // Try to extract from page title or content for basic keywords
    const title = document.title.toLowerCase();
    const basicKeywords = [];
    
    // Add some common Tyk-related keywords based on title
    if (title.includes('api')) basicKeywords.push('API');
    if (title.includes('gateway')) basicKeywords.push('API Gateway');
    if (title.includes('dashboard')) basicKeywords.push('Dashboard');
    if (title.includes('tyk')) basicKeywords.push('Tyk');
    if (title.includes('documentation')) basicKeywords.push('Documentation');
    
    return basicKeywords;
  }

  // Helper function to get dates
  function getPublishDate() {
    const datePublished = getMetaContent('article:published_time');
    if (datePublished) {
      return new Date(datePublished).toISOString().split('T')[0];
    }
    // Default to a reasonable date for documentation
    return '2024-01-01';
  }

  function getModifiedDate() {
    const dateModified = getMetaContent('article:modified_time');
    if (dateModified) {
      return new Date(dateModified).toISOString().split('T')[0];
    }
    // Use current date as modified date
    return new Date().toISOString().split('T')[0];
  }

  // Wait for DOM to be ready
  function initStructuredData() {
    // Build structured data object
    const structuredData = {
      "@context": "https://schema.org",
      "@type": "WebPage",
      "mainEntityOfPage": {
        "@type": "WebPage",
        "@id": window.location.origin
      },
      "name": document.title,
      "headline": document.title,
      "description": getPageSummary(),
      "inLanguage": "en-US",
      "author": {
        "@type": "Organization",
        "name": "Tyk"
      },
      "copyrightHolder": {
        "@type": "Organization",
        "name": "Tyk"
      },
      "url": window.location.href,
      "keywords": getKeywords(),
      "datePublished": getPublishDate(),
      "dateModified": getModifiedDate()
    };

    // Remove empty keywords array if no keywords found
    if (structuredData.keywords.length === 0) {
      delete structuredData.keywords;
    }

    // Check if structured data already exists to avoid duplicates
    const existingScript = document.querySelector('script[type="application/ld+json"]');
    if (existingScript) {
      return; // Don't add duplicate structured data
    }

    // Inject structured data into head
    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.textContent = JSON.stringify(structuredData, null, 2);
    document.head.appendChild(script);

    // Debug log (remove in production)
    console.log('Tyk Docs: Structured data added', structuredData);
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStructuredData);
  } else {
    initStructuredData();
  }
})();
