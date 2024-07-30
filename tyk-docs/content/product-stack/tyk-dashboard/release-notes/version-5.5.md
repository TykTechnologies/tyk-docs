---
title: Tyk Dashboard 5.5 Release Notes
date: 2024-03-27T15:51:11Z
description: "Release notes documenting updates, enhancements, and changes for Tyk Dashboard versions within the 5.5.X series."
tags: ["Tyk Dashboard", "Release notes", "v5.5", "5.5.0", "5.5", "changelog"]
---
<!-- Required. oss or licensed. Choose one of the following:
    **Licensed Protected Product**
    Or
    ****Open Source** ([Mozilla Public License](https://github.com/TykTechnologies/tyk/blob/master/LICENSE.md))**
-->

**This page contains all release notes for version 5.5.X displayed in a reverse chronological order**

## Support Lifetime

Our minor releases are supported until our next minor comes out.

---
## 5.5.0 Release Notes
### Release Date xxx
### Breaking Changes
<!-- Required. Use the following statement if there are no breaking changes, or explain if there are -->
**Attention: Please read this section carefully**
There are no breaking changes in this release.

### Dependencies {#dependencies-5.5.0}
<!--Required. Use this section to announce the following types of dependencies compatible with the release:
Version compatibility with other components in the Tyk stack. This takes the form of a compatibility matrix and is only required for Gateway and Portal.
3rd party dependencies and tools -->
#### Compatibility Matrix For Tyk Components
<!-- Required. Version compatibility with other components in the Tyk stack. This takes the form of a compatibility matrix and is only required for Gateway and Portal.
An illustrative example is shown below. -->
| Dashboard Version | Recommended Releases | Backwards Compatibility |
|----    |---- |---- |
| 5.5.0 | MDCB v2.6.0     | MDCB v2.5.1 |
|         | Operator v0.18 | Operator v0.17 |
|         | Sync v1.5.0   | Sync v1.4.3 |
|         | Helm Chart v1.5.0 | Helm all versions |
| | EDP v1.10.0 | EDP all versions |
| | Pump v1.10.0 | Pump all versions |
| | TIB (if using standalone) v1.5.1 | TIB all versions |

#### 3rd Party Dependencies & Tools {#3rdPartyTools-v5.5.0}
<!-- Required. Third-party dependencies encompass tools (GoLang, Helm etc.), databases (PostgreSQL, MongoDB etc.) and external software libraries. This section should be a table that presents the third-party dependencies and tools compatible with the release. Compatible is used in the sense of those versions tested with the releases. Such information assists customers considering upgrading to a specific release.

Additionally, a disclaimer statement was added below the table, for customers to check that the third-party dependency they decide to install remains in support.

An example is given below for illustrative purposes only. Tested Versions and Compatible Versions information will require discussion with relevant squads and QA. -->

| Third Party Dependency                                     | Tested Versions        | Compatible Versions    | Comments | 
| ---------------------------------------------------------- | ---------------------- | ---------------------- | -------- | 
| [GoLang](https://go.dev/dl/)                               | 1.21       | 1.21       | [Go plugins]({{< ref "plugins/supported-languages/golang" >}}) must be built using Go 1.21 | 
| [Redis](https://redis.io/download/)  | 6.2.x, 7.x  | 6.2.x, 7.x  | Used by Tyk Dashboard | 
| [MongoDB](https://www.mongodb.com/try/download/community)  | 5.0.x, 6.0.x, 7.0.x  | 5.0.x, 6.0.x, 7.0.x  | Used by Tyk Dashboard | 
| [PostgreSQL](https://www.postgresql.org/download/)         | 12.x - 16.x LTS        | 12.x - 16.x            | Used by Tyk Dashboard | 
| [OpenAPI Specification](https://spec.openapis.org/oas/v3.0.3) | v3.0.x      | v3.0.x          | Supported by [Tyk OAS]({{< ref "tyk-apis/tyk-gateway-api/oas/x-tyk-oas-doc" >}})|

### Deprecations
<!-- Required. Use the following statement if there are no deprecations, or explain if there are -->
There are no deprecations in this release.
<!-- Optional section!
Used to share and notify users about our plan to deprecate features, configs etc.
Once you put an item in this section, we must keep this item listed in all the following releases till the deprecation happens. -->
<!-- ##### Future deprecations
-->
### Upgrade instructions {#upgrade-5.5.0}
If you are upgrading to 5.5.0, please follow the detailed [upgrade instructions](#upgrading-tyk).
Add upgrade steps here if necessary.

### Release Highlights
<!-- Required. Use similar ToV to previous release notes. For example for a patch release:
This release primarily focuses on bug fixes.
For a comprehensive list of changes, please refer to the detailed [changelog]({{< ref "#Changelog-vX.Y.0">}}) below.
-->
We are excited to announce Tyk Dashboard 5.5, featuring a brand-new dashboard identity, advanced rate-limiting capabilities, and enhanced security options. For a comprehensive list of changes, please refer to the change log below.

#### New Dashboard brand identity

Experience a refreshed and modern look with our updated dashboard brand identity. The new design enhances usability and provides a cleaner, more intuitive interface for managing your APIs.

#### Implemented Upstream Endpoint rate limits

 Introduced new controls to configure rate limits at the endpoint level for both Tyk OAS and Tyk Classic APIs. This feature allows for more granular protection of upstream services from abuse, similar to Tyk’s traditional 'API-level' or 'Global' rate limits but applied specifically at the endpoint level.

#### Root CA support for client certificate authentication

We've added support for using root Certificate Authority (CA) certificates as client certificates in API definitions. This enhancement simplifies certificate management by allowing the system to authenticate clients with certificates signed by the configured root CA, applicable for static mutual TLS (mTLS) configurations only.

### Downloads
- [Docker Image to pull](https://hub.docker.com/r/tykio/tyk-dashboard/tags?page=&page_size=&ordering=&name=v5.5.0)
- ```bash
  docker pull tykio/tyk-dashboard:v5.5.0
  ```
- Helm charts
  - [tyk-charts v1.5]({{< ref "/product-stack/tyk-charts/release-notes/version-1.5.md" >}})

### Changelog {#Changelog-v5.5.0}
<!-- Required. The change log should include the following ordered set of sections below that briefly summarise the features, updates and fixed issues of the release.
Here it is important to explain the benefit of each changelog item. As mentioned by James in a previous Slack message (https://tyktech.slack.com/archives/C044R3ZTN6L/p1686812207060839?thread_ts=1686762128.651249&cid=C044R3ZTN6L):
"...it is important to document the customer impact for the work delivered, so we can share it with prospects/install base. For example:
"New Chart delivers x and y benefit to a and b customer use cases. The business impact for them will be this and that" -->
#### Added
<!-- This section should be a bullet point list of new features. Explain:
- The purpose of the new feature
- How does the new feature benefit users?
- Link to documentation of the new feature
- For OSS - Link to the corresponding issue if possible on GitHub to allow the users to see further info.
Each change log item should be expandable. The first line summarises the changelog entry. It should be then possible to expand this to reveal further details about the changelog item. This is achieved using HTML as shown in the example below. -->
<ul>
<li>
<details>
<summary>Dashboard support for upstream endpoint rate limits Added</summary>

Introduced a UI for configuring the new upstream endpoint rate limit middleware in the OAS Designer.
</details>
</li>
<details>
<summary>Enhancement: Root CA Support for client certificate authentication</summary>

We've added support for using root Certificate Authority (CA) certificates as client certificates in API definitions. The system now authenticates clients with certificates signed by the configured root CA, simplifying certificate management for multiple clients sharing a common CA. This functionality is available for static mutual TLS (mTLS) configurations only.
</details>
</li>
<details>
<summary> Implemented upstream endpoint rate limits</summary>

Added new controls to configure rate limits at the endpoint level for both Tyk OAS and Tyk Classic APIs. This feature aims to protect upstream services from abuse, providing the same functionality as Tyk’s traditional 'API-level' or 'Global' rate limits but at a more granular level.
</details>
</li>
<details>
<summary>Updated NPM packages for React v18</summary>

Updated npm packages for the Dashboard UI application to support React v18.
</details>
</li>
<details>
<summary>Corrected ordering of OAS API paths to prevent Middleware misapplication</summary>

Fixed an issue where nested API endpoints, such as '/test' and '/test/abc', might incorrectly apply middleware from the parent path to the nested path. The fix ensures that API endpoint definitions are correctly ordered, preventing this middleware misapplication and ensuring both the HTTP method and URL match accurately.
</details>
</li>
<details>
<summary>Enhanced API versioning with fallback option for 'First of Path' version data location</summary>

Introduced a new configuration for API versioning with 'url_versioning_pattern'. This regex-based field helps identify if the first part of a URL is a version pattern, improving control over 'strip_versioning_data' and 'fallback_to_default' functionalities.
</details>
</li>
<li>
<details>
<summary>Improved Schema editor functionality for GQL APIs</summary>

We've expanded the functionality of the schema editor for GQL APIs. Users can now easily import their schema from a file, export it, or quickly clean the entire editor if a mistake is made.
</details>
</li>
</ul>

#### Fixed
<!-- This section should be a bullet point list that describes the issues fixed in the release. For each fixed issue explain:
- What problem the issue caused
- How was the issue fixed
- Link to (new) documentation created as a result of a fix. For example, a new configuration parameter may have been introduced and documented for the fix
- For OSS - Link to the corresponding issue if possible on GitHub to allow the users to see further info.
Each change log item should be expandable. The first line summarises the changelog entry. It should be then possible to expand this to reveal further details about the changelog item. This is achieved using HTML as shown in the example below. -->
<ul>
<li>
<details>
<summary>Resolved SSE streaming issue</summary>

Addressed a bug that caused Server Side Event (SSE) streaming responses to be considered for caching, which required buffering the response and prevented SSE from being correctly proxied.
</details>
</li>
<li>
<details>
<summary>Classic raw editor gains Endpoint rate limiter configuration</summary>

Added functionality for users to configure rate limits per endpoint using the raw API definition for classic Tyk APIs.
</details>
</li>
<li>
<details>
<summary>Save API button now visible for all users</summary>

Addressed an issue in SSO where user permissions were not correctly applied, ensuring the Save API button is visible to all users in the Dashboard UI.
</details>
</li>
<li>
<details>
<summary>Public playground schema exposure fixed with Introspection disabled</summary>

Resolved an issue where the Public GQL Playground displayed schema information despite introspection being turned off. Now, schema details are hidden unless valid authentication credentials are provided, ensuring a secure and consistent user experience.
</details>
</li>
</ul>

#### Security Fixes
<!-- This section should be a bullet point list that should be included when any security fixes have been made in the release, e.g. CVEs. For CVE fixes, consideration needs to be made as follows:
1. Dependency-tracked CVEs - External-tracked CVEs should be included on the release note.
2. Internal scanned CVEs - Refer to the relevant engineering and delivery policy.
For agreed CVE security fixes, provide a link to the corresponding entry on the NIST website. For example:
- Fixed the following CVEs:
    - [CVE-2022-33082](https://nvd.nist.gov/vuln/detail/CVE-2022-33082)
-->
<ul>
<li>
<details>
<summary>High priority CVEs fixed</summary>
Fixed the following high priority CVEs identified in the Tyk Dashboard, providing increased protection against security vulnerabilities:
- [CVE-2023-39325](https://nvd.nist.gov/vuln/detail/CVE-2023-39325)
- [CVE-2023-45283](https://nvd.nist.gov/vuln/detail/CVE-2023-45283)
</details>
</li>
</ul>
<!-- Required. use 3 hyphens --- between release notes of every patch (minors will be on a separate page) -->
---
<!--
Repeat the release notes section above for every patch here
-->
<!-- The footer of the release notes page. It contains a further information section with details of how to upgrade Tyk,
links to API documentation and FAQs. You can copy it from the previous release. -->

## Further Information

### Upgrading Tyk
Please refer to the [upgrading Tyk]({{< ref "upgrading-tyk" >}}) page for further guidance on the upgrade strategy.

### API Documentation
<!-- Required. Update the link to the Gateway "tyk-gateway-api" or dashboard "tyk-dashboard-api" and the Postman collection

If there were changes in any of Tyk’s API docs:

- Have API endpoints been documented in the release note summary and changelog?				
- Has a link to the endpoint documentation being included?
- Has the benefit of the new/updated endpoint been explained in the release highlights and changelog?
-->
- [OpenAPI Document]({{<ref "tyk-dashboard-api/" >}})
- [Postman Collection](https://www.postman.com/tyk-technologies/workspace/tyk-public-workspace/overview)

### FAQ
Please visit our [Developer Support]({{< ref "frequently-asked-questions/faq" >}}) page for further information relating to reporting bugs, upgrading Tyk, technical support and how to contribute.



