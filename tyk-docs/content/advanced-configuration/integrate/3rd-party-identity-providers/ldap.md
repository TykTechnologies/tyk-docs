---
date: 2017-03-24T17:02:11Z
title: Lightweight Directory Access Protocol (LDAP)
menu:
  main:
    parent: "3rd Party Identity Providers"
weight: 0
aliases:
  - /integrate/3rd-party-identity-providers/dashboard-login-ldap-tib/
  - /integrate/3rd-party-identity-providers/openldap/
---

The Lightweight Directory Access Protocol (LDAP) is a standard protocol that maintains and provides access to "directory services" within a network. An LDAP Identity Provider (IdP) enables you to bind a user to an LDAP server based on a username and password configuration. The LDAP provider currently does not extract user data from the server to populate a user object, but will provide enough defaults to work with all handlers.

## Log into the Dashboard using LDAP

This is an example of a TIB profile that could be used to log a user into the Dashboard using an LDAP pass-through provider:

```.json
{
  "ActionType": "GenerateOrLoginUserProfile",
  "ID": "4",
  "OrgID": "{YOUR-ORG-ID}",
  "IdentityHandlerConfig": {
		"DashboardCredential": "ADVANCED-API-USER-API-TOKEN"
  },
  "ProviderConfig": {
    "FailureRedirect": "http://{DASH-DOMAIN}:{DASH-PORT}/?fail=true",
    "LDAPAttributes": [],
    "LDAPPort": "389",
    "LDAPServer": "localhost",
    "LDAPUserDN": "cn=*USERNAME*,cn=dashboard,ou=Group,dc=test-ldap,dc=tyk,dc=io"
  },
  "ProviderName": "ADProvider",
  "ReturnURL": "http://{DASH-DOMAIN}:{DASH-PORT}/tap",
  "Type": "passthrough" 
}

```

The only step necessary to perform this is to send a `POST` request to the LDAP URL.

TIB can pull a username and password out of a request in two ways:
1.  Two form fields: `username` and `password`
2.  A basic auth header using the Basic Authentication standard form

By default, TIB will look for the two form fields. To enable Basic Auth header extraction, add `"GetAuthFromBAHeader": true` to the `ProviderConfig` section.

If you make this request with a valid user that can bind to the LDAP server, Tyk will redirect the user to the dashboard with a valid session. There's no more to it, this mechanism is pass-through and is transparent to the user, with TIB acting as a direct client to the LDAP provider.

{{< note success >}}
**Note**  

The `LDAPUserDN` field MUST contain the special `*USERNAME*` marker in order to construct the users DN properly.
{{< /note >}}

There is a full worked example for using LDAP to login to the Tyk Dashboard [here]({{< ref "advanced-configuration/integrate/3rd-party-identity-providers/dashboard-login-ldap-tib" >}}).

## Generate an OAuth token using LDAP

The configuration below will take a request that is posted to TIB and authenticate it against LDAP. If the request is valid it will redirect to the Tyk Gateway OAuth client's `Redirect URI` with the token provided as a URL fragment:

```.json
{
  "ActionType": "GenerateOAuthTokenForClient",
  "ID": "6",
  "IdentityHandlerConfig": {
    "DashboardCredential": "{DASHBAORD-API-ID}",
    "DisableOneTokenPerAPI": false,
    "OAuth": {
      "APIListenPath": "{API-LISTEN-PATH}",
      "BaseAPIID": "{BASE-API-ID}",
      "ClientId": "{TYK-OAUTH-CLIENT-ID}",
      "RedirectURI": "http://{APP-DOMAIN}:{PORT}/{AUTH-SUCCESS-PATH}",
      "ResponseType": "token",
      "Secret": "{TYK-OAUTH-CLIENT-SECRET}"
    }
  },
  "MatchedPolicyID": "POLICY-ID",
  "OrgID": "53ac07777cbb8c2d53000002",
  "ProviderConfig": {
    "FailureRedirect": "http://{APP-DOMAIN}:{PORT}/failure",
    "LDAPAttributes": [],
    "LDAPPort": "389",
    "LDAPServer": "localhost",
    "LDAPUserDN": "cn=*USERNAME*,cn=dashboard,ou=Group,dc=ldap,dc=tyk-ldap-test,dc=com"
  }
  "ProviderName": "ADProvider",
  "ReturnURL": "",
  "Type": "passthrough"
}
```

This configuration is useful for internal APIs that need valid OAuth tokens (e.g. a webapp or mobile app) that require validation by an LDAP provider.

## Log into the Classic Portal using LDAP

LDAP requires little configuration, we can use the same provider configuration that we used to log into the Dashboard to target the Classic Portal instead - notice the change in the handler configuration and the return URL:

```json
{
  "ActionType": "GenerateOrLoginDeveloperProfile",
  "ID": "5",
  "IdentityHandlerConfig": {
    "DashboardCredential": "822f2b1c75dc4a4a522944caa757976a"
  },
  "OrgID": "53ac07777cbb8c2d53000002",
  "ProviderConfig": {
    "FailureRedirect": "http://{PORTAL-DOMAIN}:{PORTAL-PORT}/portal/login/",
    "LDAPAttributes": [],
    "LDAPPort": "389",
    "LDAPServer": "localhost",
    "LDAPUserDN": "cn=*USERNAME*,cn=dashboard,ou=Group,dc=test-ldap,dc=tyk,dc=io"
  },
  "ProviderConstraints": {
    "Domain": "",
    "Group": ""
  },
  "ProviderName": "ADProvider",
  "ReturnURL": "http://{PORTAL-DOMAIN}:{PORTAL-PORT}/portal/sso/",
  "Type": "passthrough"
}
```

Once again, a simple `POST` request is all that is needed to validate a user via an LDAP provider.

## Using advanced LDAP search

In some cases the validation of a user CN is not enough, and you also need to verify that a user matches some specific rules, such as an internal team ID. In this case TIB can support additional LDAP search checks, and if the result of this search returns only 1 record, it will pass the user.

To perform an advanced LDAP search, you need to specify three additional attributes in the profile configuration file:
- `LDAPBaseDN`: the base DN used for doing LDAP search, for example `cn=dashboard,ou=Group`
- `LDAPFilter`: the filter to be applied to the search, this should include the `*USERNAME*`variable. For example: `((objectCategory=person)(objectClass=user)(cn=*USERNAME*))`
- `LDAPSearchScope`: this specifies the portion of the target subtree that should be considered. Supported search scope values include: 0 - baseObject (often referred to as "base"), 1 - singleLevel (often referred to as "one"), 2 - wholeSubtree (often referred to as "sub")

For additional information about [LDAP search protocol](https://www.ldap.com/the-ldap-search-operation)

Example profile using LDAP search filters:
```json
{
	"ActionType": "GenerateOAuthTokenForClient",
	"ID": "2",
	"IdentityHandlerConfig": {
		"DashboardCredential": "ADVANCED-API-USER-API-TOKEN",
		"DisableOneTokenPerAPI": false,
		"OAuth": {
			"APIListenPath": "oauth-1",
			"BaseAPIID": "API-To-GRANT-ACCESS-TO",
			"ClientId": "TYK-OAUTH-CLIENT-ID",
			"RedirectURI": "http://your-app-domain.com/target-for-fragment",
			"ResponseType": "token",
			"Secret": "TYK-OAUTH-CLIENT-SECRET"
		}
	},
	"MatchedPolicyID": "POLICY-TO-ATTACH-TO-KEY",
	"OrgID": "53ac07777cbb8c2d53000002",
	"ProviderConfig": {
		"FailureRedirect": "http://yourdomain.com/failure-url",
		"LDAPAttributes": [],
		"LDAPBaseDN": "cn=dashboard,ou=Group,dc=ldap,dc=tyk-test,dc=com",
		"LDAPEmailAttribute": "mail",
		"LDAPSearchScope": 2,
		"LDAPFilter": "(&(objectcategory=user)(sAMAccountName=*USERNAME*)(memberOf=CN=RL - PAT - T1-00002,OU=Role,OU=Security Roles,DC=company,DC=net))",
		"LDAPPort": "389",
		"LDAPServer": "ldap.company.com",
		"LDAPUserDN": "*USERNAME*@company.com"
	},
	"ProviderName": "ADProvider",
	"ReturnURL": "",
	"Type": "passthrough"
}
```
