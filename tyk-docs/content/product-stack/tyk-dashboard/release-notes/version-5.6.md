---
title: Tyk Dashboard 5.6 Release Notes
date: 2024-03-27T15:51:11Z
description: "Release notes documenting updates, enhancements, and changes for Tyk Dashboard versions within the 5.6.X series."
tags: ["Tyk Dashboard", "Release notes", "v5.6", "5.6.0", "5.6", "changelog"]
---
<!-- Required. oss or licensed. Choose one of the following:
    **Licensed Protected Product**
    Or
    ****Open Source** ([Mozilla Public License](https://github.com/TykTechnologies/tyk/blob/master/LICENSE.md))**
-->

**This page contains all release notes for version 5.6.X displayed in a reverse chronological order**

## Support Lifetime

Our minor releases are supported until our next minor comes out.

---
## 5.6.0 Release Notes

### Release Date xxx

### Breaking Changes
<!-- Required. Use the following statement if there are no breaking changes, or explain if there are -->

There are no breaking changes in this release.

### Dependencies {#dependencies-5.6.0}
<!--Required. Use this section to announce the following types of dependencies compatible with the release:
Version compatibility with other components in the Tyk stack. This takes the form of a compatibility matrix and is only required for Gateway and Portal.
3rd party dependencies and tools -->
#### Compatibility Matrix For Tyk Components
<!-- Required. Version compatibility with other components in the Tyk stack. This takes the form of a compatibility matrix and is only required for Gateway and Portal.
An illustrative example is shown below. -->
| Dashboard Version | Recommended Releases | Backwards Compatibility |
|----    |---- |---- |
| 5.6.0 | MDCB v2.7 - TBP    | MDCB v2.5.1 |
|         | Operator v0.18 - TBP | Operator v0.17 |
|         | Sync v1.5 - TBP   | Sync v1.4.3 |
|         | Helm Chart v1.6 - TBP | Helm all versions |
| | EDP v1.10 | EDP all versions |
| | Pump v1.11 | Pump all versions |
| | TIB (if using standalone) v1.5.1 | TIB all versions |

#### 3rd Party Dependencies & Tools {#3rdPartyTools-v5.6.0}
<!-- Required. Third-party dependencies encompass tools (GoLang, Helm etc.), databases (PostgreSQL, MongoDB etc.) and external software libraries. This section should be a table that presents the third-party dependencies and tools compatible with the release. Compatible is used in the sense of those versions tested with the releases. Such information assists customers considering upgrading to a specific release.

Additionally, a disclaimer statement was added below the table, for customers to check that the third-party dependency they decide to install remains in support.

An example is given below for illustrative purposes only. Tested Versions and Compatible Versions information will require discussion with relevant squads and QA. -->

| Third Party Dependency                                     | Tested Versions        | Compatible Versions    | Comments | 
| ---------------------------------------------------------- | ---------------------- | ---------------------- | -------- | 
| [GoLang](https://go.dev/dl/)                               | 1.22       | 1.22       | [Go plugins]({{< ref "plugins/supported-languages/golang" >}}) must be built using Go 1.22 | 
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
### Upgrade instructions {#upgrade-5.6.0}
If you are upgrading to 5.6.0, please follow the detailed [upgrade instructions](#upgrading-tyk). 

### Release Highlights
<!-- Required. Use similar ToV to previous release notes. For example for a patch release:
This release primarily focuses on bug fixes.
For a comprehensive list of changes, please refer to the detailed [changelog]({{< ref "#Changelog-vX.Y.0">}}) below.
-->
We are thrilled to announce new updates and improvements in Tyk 5.6.0, bringing more control, flexibility, and performance.  For a comprehensive list of changes, please refer to the detailed [changelog]({{< ref "#Changelog-v5.6.0">}}) below.

#### Per endpoint Rate Limiting for clients

We’ve introduced client-level per-endpoint rate limits. Rate limits can now be configured in security policies and keys, and are applicable to both Tyk OAS and Tyk Classic APIs, offering greater control over how resources are accessed.

#### Go upgrade to 1.22

We’ve upgraded the Tyk Gateway and Tyk Dashboard to Golang 1.22, bringing improved performance, better security, and enhanced stability to the core system.

#### Enhanced Role-Based Access Controls (RBAC) in Tyk Dashboard

We’ve enhanced Role-Based Access Controls (RBAC) in the Tyk Dashboard to improve security. Now, only super-admins can create new admins, admin roles can't be assigned to user groups, and password resets are limited to admin users within their organization.


### Downloads
- [Docker Image to pull](https://hub.docker.com/r/tykio/tyk-dashboard/tags?page=&page_size=&ordering=&name=v5.6.0)
- ```bash
  docker pull tykio/tyk-dashboard:v5.6.0
  ```
- Helm charts
  - TBP (To Be Published separately after the release)

### Changelog {#Changelog-v5.6.0}
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
<summary>Endpoint-Level Rate Limits for Client Control</summary>

We have introduced support for configuring endpoint-level rate limits in keys and policies. This new feature allows for more granular control over client consumption of API resources, enabling you to manage and optimize API usage more effectively. 
</details>
</li>
</ul>

#### Changed

<!-- This should be a bullet-point list of updated features. Explain:

- Why was the update necessary?
- How does the update benefit users?
- Link to documentation of the updated feature
- For OSS - Link to the corresponding issue if possible on GitHub to allow the users to see further info.

Each change log item should be expandable. The first line summarises the changelog entry. It should be then possible to expand this to reveal further details about the changelog item. This is achieved using HTML as shown in the example below. -->
<ul>
<li>
<details>
<summary>Upgrade to Go 1.22 for Tyk Dashboard</summary>

The Tyk Dashboard has been upgraded from Golang 1.21 to Golang 1.22, bringing enhanced performance, strengthened security, and access to the latest features available in the new Golang release.
</details>
</li>
<li>
<details>
<summary>Swagger Update: Enhanced Documentation and Schema for Dashboard</summary>

We have updated the swagger.yml schema for the Dashboard to reflect the latest changes in product endpoints, payloads, and responses. This update includes new fields and endpoints, improved examples, documentation adjustments, and fixes for schema issues. These enhancements aim to improve usability and ensure that the documentation accurately represents the current code state.
</details>
</li>

<li>
<details>
<summary>UI Update: Renamed "Playground" Tab to "Playgrounds"</summary>

The "Playground" tab in the API Designer has been renamed to "Playgrounds." This change consolidates access to both internal and external playgrounds within a single section, offering a more streamlined and intuitive experience for API design and testing.
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
<summary>Correct Combination of Client Endpoint Rate Limits in Policies</summary>

We have fixed an issue where API-level rate limits set in multiple policies were not correctly applied to the same key. With this update, when multiple policies configure rate limits for a key, the key will now receive the highest rate limit from the combined policies, ensuring proper enforcement of limits.
</details>
</li>
<li>
<details>
<summary>Dashboard and Postgres Average Usage Per API</summary>

- Resolved an issue where 429 status codes were not being displayed on the Activity Overview page.
- Fixed portal graphs when using Postgres by adding a default "day" grouping resolution to the query.
- Corrected issues with the Error Breakdown related to date parameters, ensuring accurate date handling and display.

</details>
</li>

<li>
<details>
<summary>UI Fix: Tyk Dashboard Keys Page Now Displays with 10+ Policies</summary>

We have resolved an issue in the Tyk Dashboard where the Keys page would display a blank screen if more than 10 policies were associated with a key. The UI has been updated to correctly handle and display the page even when a key is linked to more than 10 policies, ensuring better visibility and management.

</details>
</li>

<li>
<details>
<summary>UI Fix: Prevented Multiple Versions of the Same Tyk Classic API from Being Added to a Policy</summary>

We have fixed an issue in the Dashboard UI that allowed users to attach the same version of a Tyk Classic API multiple times to a policy. The UI now correctly restricts duplicate API versions, ensuring accurate policy configuration and management.

</details>
</li>

<li>
<details>
<summary>UI Fix: Corrected JWT Scope to Policy Mapping in Dashboard</summary>

We have resolved an issue in the Dashboard UI where the scope name was incorrectly recorded instead of the policy ID for subsequent JWT scope mappings. The UI now accurately associates the defined scope with the correct policy, ensuring proper JWT scope to policy mappings.

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
<summary>Strengthened ResetPassword Permission Behavior</summary>

We have fixed a privilege escalation vulnerability where a user with certain permissions could potentially reset other users' passwords, including admin accounts. The following changes have been made to tighten the behavior of the ResetPassword permission within the Dashboard's Role-Based Access Control (RBAC) system:
- Only super-admins or admins can assign admin status to a user, and this cannot be assigned to user groups.
- All users can reset their own passwords, but resetting other users' passwords now requires a specific ResetPassword permission.
- The scope of the ResetPassword permission is limited to the Tyk Organization (OrgId) for which the user is an admin.
- The ResetPassword permission can only be assigned by super-admins, directly to admin users (not user groups).
- The allow_admin_reset_password configuration ensures that all admin users automatically receive the ResetPassword permission.

</details>
</li>

<li>
<details>
<summary>Gateway Secret No Longer Logged in Dashboard Logs</summary>

We have addressed a security issue where the Gateway secret was appearing in the Dashboard system logs when the /api/keys endpoint was called while in debug mode. This fix prevents the Gateway secret from being logged, enhancing the security of your system. Please note that running in debug mode is not recommended for production environments.

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



