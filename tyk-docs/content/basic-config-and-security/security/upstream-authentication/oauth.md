---
title: Upstream OAuth Authentication
tags: ["upstream-oauth-auth"]
description: "How to authenticate upstream requests with OAuth authentication"
menu:
  main:
    parent: "Upstream Authentication"
weight: 3
---

If your upstream API is protected with OAuth authentication, you can configure Tyk to send requests with OAuth authentication credentials.

## How To Set Up

### Via API Definition

Inside your OAS API definition you should configure `x-tyk-api-gateway.upstream.authentication.oauth` field.

### Client Credentials Grant

To use the client credentials grant type, configure the following fields:

- `enabled` needs to be true to enable OAuth authentication.
- `allowedAuthorizeTypes` should include `clientCredentials`.
- `clientCredentials` should be configured with:
    - `header.enabled` set to true.
    - `header.name` is the header to be used.
    - `tokenUrl` is the URL to obtain the token.
    - `clientId` is the client ID to be used.
    - `clientSecret` is the client secret to be used.
    - `scopes` is an array of scopes to be requested.
    - `extraMetadata` is an array of additional fields to be read from the OAuth provider response and saved to the request context.

Example:
```json
{
  "x-tyk-api-gateway": {
    "upstream": {
      "authentication": {
        "enabled": true,
        "oauth": {
          "allowedAuthorizeTypes": [
            "clientCredentials"
          ],
          "clientCredentials": {
            "header": {
              "enabled": true,
              "name": "Authorization"
            },
            "tokenUrl": "http://salesforce.com",
            "clientId": "client123",
            "clientSecret": "secret123",
            "scopes": ["scope1"],
            "extraMetadata": ["instance_url"]
          }
        }
      }
    }
  }
}
```

### Password Grant

To use the password grant type, configure the following fields:
- `enabled` needs to be true to enable OAuth authentication.
- `allowedAuthorizeTypes` should include `password`.
- `password` should be configured with:
  - `header.enabled` set to true.
  - `header.name` is the header to be used.
  - `tokenUrl` is the URL to obtain the token.
  - `clientId` is the client ID to be used.
  - `clientSecret` is the client secret to be used.
  - `scopes` is an array of scopes to be requested.
  - `username` is the username to be used.
  - `password` is the password to be used.
  - `extraMetadata` is an array of additional fields to read from the OAuth provider response and saved to the request context.


Example:
```json
{
  "x-tyk-api-gateway": {
    "upstream": {
      "authentication": {
        "oauth": {
          "enabled": true,
          "allowedAuthorizeTypes": [
            "password"
          ],
          "password": {
            "header": {
              "enabled": true,
              "name": "Authorization"
            },
            "tokenUrl": "http://salesforce.com",
            "clientId": "client123",
            "clientSecret": "secret123",
            "scopes": ["scope1"],
            "username": "user",
            "password": "pass",
            "extraMetadata": ["instance_url"]
          }
        }
      }
    }
  }
}
```

**Note**
If the `extraMetadata` field is configured, the response from the OAuth provider will be parsed and the fields specified in the `extraMetadata` array will be saved to the request context.
Those fields can be accessed in the middlewares (e.g. URL Rewrite) via the $tyk_context object.
In our use case, the `instance_url` field will be saved to the request context and can be accessed in the URL Rewrite middleware as `$tyk_context.instance_url`.
However, when creating a matching rule based on Request Context in the URL Rewrite middleware, the field identifier is just `instance_url` as $tyk_context is implied.


