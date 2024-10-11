---
title: Upstream Basic Authentication
tags: ["upstream-basic-auth"]
description: "How to authenticate upstream requests with basic authentication"
menu:
  main:
    parent: "Upstream Authentication"
weight: 2
---

If your upstream API is protected with basic authentication, you can configure Tyk to send requests with basic authentication credentials.

- You can specifiy username and password to be used. 
- You can configure the header in which basic authenticaiton credentials are to be sent, the default header to be used is `Authorization`. 


## How To Set Up

### Via API Definition

Inside your OAS API definition you should configure `x-tyk-api-gateway.upstream.authentication.basicAuth` field.
- `enabled` needs to be true to enable upstream basic authentication.
- `headerName` is the header to be used.
- `username` is the username to be used.
- `password` is the password to be used.

```
{{< note success >}}
**Note**
`x-tyk-api-gateway.upstream.authentication.enabled` needs to be true to enable upstream authentication.

If the configured `headerName` is also sent from clientside, Tyk will replace it with basic auth credentials before sending it to upstream.
{{< /note >}}
```
