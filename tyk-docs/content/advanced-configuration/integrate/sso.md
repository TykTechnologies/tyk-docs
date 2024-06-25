---
date: 2017-03-24T16:40:31Z
title: Single Sign-On
menu: 
    main:
        parent: "Tyk Dashboard"
weight: 0
---

Single Sign-On (SSO) gives users the ability to log in to multiple applications without the need to enter their password more than once.

[OpenID Connect]({{< ref "basic-config-and-security/security/authentication-authorization/openid-connect" >}}) (OIDC) and Security Assertion Markup Language (SAML) enables an application (such as Tyk Dashboard) to verify the identity of users without having to manage usernames and passwords locally, by offloading the identification process and secure storage of user credentials to a dedicated Identity Provider (IdP). The Authorisation server of the IdP identifies the users for a pre-registered and approved application (`client` in OAuth and OIDC terminology).

[Tyk Identity Broker]({{< ref "tyk-identity-broker" >}}) is an open-source project that can be used to integrate Tyk Dashboard and Classic Portal with 3rd party identity providers (IDPs). TIB has been included as a built-in feature of the Tyk Dashboard since Tyk 3.0: no configuration is required and it is readily available for use.

TIB allows you to implement single sign-on and use your existing user directory for login to the Tyk products. It has been designed as a glue-code solution, so it can integrate with almost any IdP.
<br>
<br>
{{< note success >}}
**Note**  

To find out how to integrate with 3rd Party IdPs using different protocols, check out [this section]({{< ref "advanced-configuration/integrate/3rd-party-identity-providers" >}}).
<br>
<br>
For worked examples of specific 3rd Party integrations, including Auth0 and Okta, check out [this section]({{< ref "advanced-configuration/integrate" >}}).
{{< /note >}}

## How SSO works with Tyk Dashboard

Once you have configured the integration between Tyk Dashboard and your Identity Provider (typically using Tyk Identity Broker) then your users can simply log into Tyk Dashboard through your IdP.

You can set custom login pages for the Dashboard and Classic Portal using the `sso_custom_login_url` and `sso_custom_portal_login_url` options respectively in the Tyk Dashboard config file (`tyk_analytics.conf`).

## SSO user permissions

Logging in via SSO will grant the user **admin** rights in Tyk Dashboard, giving the user full access to configure and control the Dashboard.

You may not want all SSO users to assume administrator rights to your Tyk Dashboard, so you can configure alternative [default permissions](#setting-default-sso-permissions) that will be inherited instead. Of course, you might want certain users to have additional permissions (for example, your admin users) and so you can also assign [per-user permissions](#setting-user-specific-permissions).

### Setting default SSO permissions

The `sso_permission_defaults` option can be configured in the Tyk Dashboard config file (`tyk_analytics.conf`) to specify the [user permissions]({{< ref "basic-config-and-security/security/dashboard/user-roles" >}}) that should be granted to SSO users.

This option has the following format:

```
"sso_permission_defaults": {
  "analytics": "read",
  "apis": "write",
  "hooks": "write",
  "idm": "write",
  "keys": "write",
  "policies": "write",
  "portal": "write",
  "system": "write",
  "users": "write",
  "user_groups": "write"
}
```

Alternatively, you can set `sso_default_group_id` in the Tyk Dashboard config file to assign SSO users to a [User Group]({{< ref "basic-config-and-security/security/dashboard/create-user-groups" >}}) where they will be granted the permissions associated with the group.

### Setting user-specific permissions

If `sso_enable_user_lookup` is set to `true` in the Tyk Dashboard config file then when someone logs in via SSO their email address is checked against all Tyk users configured in the Dashboard. If there is a match then they will inherit the permissions of that Tyk user. Thus, you can set permissions for a specific user by [creating a user]({{< ref "basic-config-and-security/security/dashboard/create-users" >}}) in the Dashboard first and assigning the required user permissions (e.g. `IsAdmin`) to this user.

## Creating a custom SSO user using Tyk Dashboard API

You can implement custom authentication schemes for the Dashboard and Classic Portal from either [Tyk Dashboard Admin API]({{< ref "tyk-apis/tyk-dashboard-admin-api/sso" >}}) or [Tyk Dashboard API]({{< ref "tyk-apis/tyk-dashboard-api/sso" >}}). The functionality of the two APIs for SSO configuration are identical, however they require a different auth header to secure requests to the API:
- the Tyk Dashboard Admin API requires an `admin-auth` header which should match the `admin-secret` parameter in `tyk_analytics.conf`
- the Tyk Dashboard API requires an `authorization` header which should match the user authentication token

Both APIs' `/sso` endpoints will generate a temporary authentication token, valid for 60 seconds, that can be used to log in to the `/tap` endpoint, or to the portal using the `<portal-url>/sso` endpoint, providing the token via the `nonce` query param. If `nonce` is valid, Tyk will create a temporary user and log them in. 

For example:
```http
GET /tap?nonce=YTNiOGUzZjctYWZkYi00OTNhLTYwODItZTAzMDI3MjM0OTEw HTTP/1.1
Host: localhost:3000    
```