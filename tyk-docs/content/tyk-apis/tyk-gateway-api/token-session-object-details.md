---
date: 2017-03-27T11:20:43+01:00
title: Token Session Object Details
menu:
  main:
    parent: "Tyk Gateway API"
weight: 2 
---

All tokens that are used to access services via Tyk correspond to a session object that informs Tyk about the context of this particular token.

A session object takes the following form:

```{.copyWrapper}
{
  "last_check": 0,
  "allowance": 1000,
  "rate": 1000,
  "per": 1,
  "expires": 1458669677,
  "quota_max": 1000,
  "quota_renews": 1458667309,
  "quota_remaining": 1000,
  "quota_renewal_rate": 3600,
  "access_rights": {
    "e1d21f942ec746ed416ab97fe1bf07e8": {
      "api_name": "Closed",
      "api_id": "e1d21f942ec746ed416ab97fe1bf07e8",
      "versions": ["Default"],
      "allowed_urls": null
    }
  },
  "org_id": "53ac07777cbb8c2d53000002",
  "oauth_client_id": "",
  "basic_auth_data": {
    "password": "",
    "hash_type": ""
  },
  "jwt_data": {
    "secret": ""
  },
  "hmac_enabled": false,
  "hmac_string": "",
  "is_inactive": false,
  "apply_policy_id": "",
  "apply_policies": [
    "59672779fa4387000129507d",
    "53222349fa4387004324324e",
    "543534s9fa4387004324324d"
    ],
  "data_expires": 0,
  "monitor": {
    "trigger_limits": null
  },
  "meta_data": {
    "test": "test-data"
  },
  "tags": ["tag1", "tag2"],
  "alias": "john@smith.com" 
}
```

* `last_check` (**deprecated**): No longer used, but this value is related to rate limiting.

* `allowance` (**deprecated**): No longer directly used, this value, no key creation, should be the same as `rate`.

* `rate`: The number of requests that are allowed in the specified rate limiting window.

* `per`: The number of seconds that the rate window should encompass.

* `expires`: A Unix timestamp that defines when the key should expire. You can set this to `0` (zero) if you don't want the key to expire.

* `quota_max`: The maximum number of requests allowed during the quota period.

* `quota_renews`: An epoch that defines when the quota renews.

* `quota_remaining`: The number of requests remaining for this user's quota (unrelated to rate limit).

* `quota_renewal_rate`: The time, in seconds. during which the quota is valid. So for `1000` requests per hour, this value would be `3600` while `quota_max` and `quota_remaining` would be `1000`.

* `access_rights`: This section is defined in the Access Control section of this documentation, use this section define what APIs and versions this token has access to.

* `org_id`: The organization this user belongs to, this can be used in conjunction with the `org_id` setting in the API Definition object to have tokens "owned" by organizations. See the Organizations Quotas section of the [Tyk Gateway API]({{< ref "tyk-gateway-api" >}}).

* `oauth_client_id`: This is set by Tyk if the token is generated by an OAuth client during an OAuth authorization flow.

* `basic_auth_data`: This section defines the basic auth password and hashing method.

* `jwt_data`: This section contains a JWT shared secret if the ID matches a JWT ID.

* `hmac_enabled`: If this token belongs to an HMAC user, this will set the token as a valid HMAC provider.

* `hmac_string`: The value of the HMAC shared secret.

* `is_inactive`: Set this value to `true` to deny access.

* `apply_policy_id` (**supported but now deprecated**): The policy ID that is bound to this token.

* `apply_policies`: This replaces `apply_policy_id` and lists your policy IDs as an array. This supports the **Multiple Policy** feature introduced in the  **v2.4 of the Gateway**.

* `data_expires`: An value, in seconds, that defines when data generated by this token expires in the analytics DB (must be using Pro edition and MongoDB).

* `monitor`: Rate monitor trigger settings, defined elsewhere in the documentation.

* `meta_data`: Metadata to be included as part of the session, this is a key/value string map that can be used in other middleware such as transforms and header injection to embed user-specific data into a request, or alternatively to query the providence of a key.

* `tags`: Tags are embedded into analytics data when the request completes. If a policy has tags, those tags will supersede the ones carried by the token (they will be overwritten).

* `alias`: As of v2.1, an Alias offers a way to identify a token in a more human-readable manner, add an Alias to a token in order to have the data transferred into Analytics later on so you can track both hashed and un-hashed tokens to a meaningful identifier that doesn't expose the security of the underlying token.
