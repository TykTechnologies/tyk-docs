---
date: 2017-03-13T15:08:55Z
Title: CORS
menu:
  main:
    parent: "API Definition Objects"
weight: 6
---


It is possible to enable CORS for certain APIs so users can make browser-based requests. The `CORS` section is added to an API definition as listed in the examples below for Tyk Gateway and Tyk Operator.

---

## Examples

{{< tabs_start >}}
{{< tab_start "Gateway API Definition" >}}
```json
"CORS": {
  "enable": true,
  "allowed_origins": [
    "http://foo.com"
  ],
  "allowed_methods": [],
  "allowed_headers": [],
  "exposed_headers": [],
  "allow_credentials": false,
  "max_age": 24,
  "options_passthrough": false,
  "debug": false
}
```
{{< tab_end >}}
{{< tab_start "Tyk Operator API Definition" >}}
```yaml {linenos=true, linenostart=1, hl_lines=["14-24"]}
apiVersion: tyk.tyk.io/v1alpha1
kind: ApiDefinition
metadata:
  name: httpbin-cors-sample
spec:
  name: httpbin-cors-sample
  use_keyless: true
  protocol: http
  active: true
  proxy:
    target_url: http://httpbin.org
    listen_path: /cors
    strip_listen_path: true
  CORS:
    enable: true
    allowed_origins:
      - "http://foo.com"
    allowed_methods: null
    allowed_headers: null
    exposed_headers: null
    allow_credentials: false
    max_age: 24
    options_passthrough: false
    debug: false
```
{{< tab_end >}}
{{< tabs_end >}}

---

## Configuration

The CORS middleware has the following options:

* `CORS.allowed_origins`: A list of origin domains to allow access from. Wildcards are also supported, e.g. `http://*.foo.com`

* `CORS.allowed_methods`: A list of methods to allow access via.

* `CORS.allowed_headers`: Headers that are allowed within a request.

* `CORS.exposed_headers`: Headers that are exposed back in the response.

* `CORS.allow_credentials`: Whether credentials (cookies) should be allowed.

* `CORS.max_age`: Maximum age of credentials.

* `CORS.options_passthrough`: allow CORS OPTIONS preflight request to be proxied directly to upstream, without authentication and rest of checks. This means that pre-flight requests generated by web-clients such as SwaggerUI or 
the Tyk Portal documentation system will be able to test the API using trial keys. If your service handles CORS natively, then enable this option.

* `debug`: If set to `true`, this option produces log files for the CORS middleware.

## Fallback values

Always keep in mind that empty arrays will fallback to some sensible defaults. If you want to avoid this, you will have to provide explicit values.
 * Fallback values for `CORS.allowed_origins`: `["*"]`
 * Fallback values for `CORS.allowed_methods`: `["GET", "POST", "HEAD"]`
 * Fallback values for `CORS.allowed_headers`: `["Origin", "Accept", "Content-Type", "X-Requested-With"]`
