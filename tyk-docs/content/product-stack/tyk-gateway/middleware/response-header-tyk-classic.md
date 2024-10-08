---
title: Using the Response Header Transform with Tyk Classic APIs
date: 2024-01-24
description: "Using the Response Header Transform middleware with Tyk Classic APIs"
tags: ["Response Header Transform", "middleware", "per-endpoint","per-API", "Tyk Classic"]
---

Tyk's [response header transform]({{< ref "advanced-configuration/transform-traffic/response-headers" >}}) middleware enables you to append or delete headers on responses received from the upstream service before sending them to the client.

There are two options for this:
- API-level modification that is applied to all responses for the API
- endpoint-level modification that is applied only to responses from a specific endpoint

{{< note success >}}
**Note**  

If both API-level and endpoint-level middleware are configured, the endpoint-level transformation will be applied first.
{{< /note >}}

When working with Tyk Classic APIs the transformation is configured in the Tyk Classic API Definition. You can do this via the Tyk Dashboard API or in the API Designer.

If you want to use dynamic data from context variables, you must [enable]({{< ref "context-variables#enabling-context-variables-for-use-with-tyk-classic-apis" >}}) context variables for the API to be able to access them from the response header transform middleware.

If you're using the newer Tyk OAS APIs, then check out the [Tyk OAS]({{< ref "product-stack/tyk-gateway/middleware/response-header-tyk-oas" >}}) page.

If you're using Tyk Operator then check out the [configuring the Response Header Transform in Tyk Operator](#tyk-operator) section below.

## Configuring the Response Header Transform in the Tyk Classic API Definition {#tyk-classic}

The API-level and endpoint-level response header transforms have a common configuration but are configured in different sections of the API definition.
{{< note success >}}

**Note**  
Prior to Tyk 5.3.0, there was an additional step to enable response header transforms (both API-level and endpoint-level). You would need to add the following to the Tyk Classic API definition:

```json
{
    "response_processors":[
        {"name": "header_injector"}
    ]
}
```

If using the Endpoint Designer in the Tyk Dashboard, this would be added automatically.

We removed the need to configure the `response_processors` element in Tyk 5.3.0.
{{< /note >}}

#### API-level transform {#tyk-classic-api}

To **append** headers to all responses from your API (i.e. for all endpoints) you must add a new `global_response_headers` object to the `versions` section of your API definition. This contains a list of key:value pairs, being the names and values of the headers to be added to responses.

To **delete** headers from all responses from your API (i.e. for all endpoints), you must add a new `global_response_headers_remove` object to the `versions` section of the API definition. This contains a list of the names of existing headers to be removed from responses.

For example:
```json  {linenos=true, linenostart=1}
{
    "version_data": {
        "versions": {
            "Default": {
                "global_response_headers": {
                    "X-Static": "foobar",
                    "X-Request-ID":"$tyk_context.request_id",
                    "X-User-ID": "$tyk_meta.uid"
                },
                "global_response_headers_remove": [
                    "X-Secret"
                ]
            }
        }
    },
}
```

This configuration will add three new headers to each response:
- `X-Static` with the value `foobar`
- `X-Request-ID` with a dynamic value taken from the `request_id` [context variable]({{< ref "context-variables" >}})
- `X-User-ID` with a dynamic value taken from the `uid` field in the [session metadata]({{< ref "getting-started/key-concepts/session-meta-data" >}})

It will also delete one header (if present) from each response:
 - `X-Secret`

#### Endpoint-level transform {#tyk-classic-endpoint}

To configure response header transformation for a specific endpoint you must add a new `transform_response_headers` object to the `extended_paths` section of your API definition.

It has the following configuration:
- `path`: the endpoint path
- `method`: the endpoint HTTP method
- `delete_headers`: a list of the headers that should be deleted from the response
- `add_headers`: a list of headers, in key:value pairs, that should be added to the response

For example:
```json  {linenos=true, linenostart=1}
{
    "transform_response_headers": [
        {
            "path": "status/200",
            "method": "GET",
            "delete_headers": ["X-Static"],
            "add_headers": [
                {"X-Secret": "the-secret-key-is-secret"},
                {"X-New": "another-header"}
            ],
        }
    ]
}
```

In this example the Response Header Transform middleware has been configured for HTTP `GET` requests to the `/status/200` endpoint. Any response received from the upstream service following a request to that endpoint will have the `X-Static` header removed and the `X-Secret` and `X-New` headers added (with values set to `the-secret-key-is-secret` and `another-header`).

#### Combining API-level and Endpoint-level transforms

If the example [API-level]({{< ref "product-stack/tyk-gateway/middleware/response-header-tyk-classic#api-level-transform" >}}) and [endpoint-level]({{< ref "product-stack/tyk-gateway/middleware/response-header-tyk-classic#endpoint-level-transform" >}}) transforms are applied to the same API, then the `X-Secret` header will be added (by the endpoint-level transform first) and then removed (by the API-level transform). Subsequently, the result of the two transforms for a call to `GET /status/200` would be to add four headers:
- `X-Request-ID`
- `X-User-ID`
- `X-Static`
- `X-New`

### Fixing response headers that leak upstream server data

A middleware called `header_transform` was added in Tyk 2.1 specfically to allow you to ensure that headers such as `Location` and `Link` reflect the outward facade of your API Gateway and also align with the expected response location to be terminated at the gateway, not the hidden upstream proxy.

This is configured by adding a new `rev_proxy_header_cleanup` object to the `response_processors` section of your API definition.

It has the following configuration:
- `headers`: a list of headers in the response that should be modified
- `target_host`: the value to which the listed headers should be updated
 
For example:
```json
{
    "response_processors": [
        {
            "name": "header_transform",
            "options": {
                "rev_proxy_header_cleanup": {
                    "headers": ["Link", "Location"],
                    "target_host": "http://TykHost:TykPort"
                }
            }
        }
    ]
}
```

In this example, the `Link` and `Location` headers will be modified from the server-generated response, with the protocol, domain and port of the value set in `target_host`.

This feature is rarely used and has not been implemented in the Tyk Dashboard UI, nor in the [Tyk OAS API]({{< ref "product-stack/tyk-gateway/middleware/response-header-tyk-oas" >}}).

## Configuring the Response Header Transform in the API Designer

You can use the API Designer in the Tyk Dashboard to configure the response header transform middleware for your Tyk Classic API by following these steps.

### API-level transform

Configuring the API-level response header transform middleware is very simple when using the Tyk Dashboard.

In the Endpoint Designer you should select the **Global Version Settings** and ensure that you have selected the **Response Headers** tab:

{{< img src="/img/dashboard/endpoint-designer/response-header-global.png" alt="Configuring the API-level response header transform" >}}

Note that you must click **ADD** to add a header to the list (for appending or deletion).

### Endpoint-level transform

##### Step 1: Add an endpoint for the path and select the Header Transform plugin

From the **Endpoint Designer** add an endpoint that matches the path for which you want to perform the transformation. Select the **Modify Headers** plugin.

{{< img src="/img/dashboard/endpoint-designer/modify-headers-plugin.png" alt="Adding the Modify Headers plugin to an endpoint" >}}

##### Step 2: Select the "Response" tab

This ensures that the transform will be applied to responses prior to them being sent to the client.

{{< img src="/img/dashboard/endpoint-designer/response-header-added.png" alt="Selecting the response header transform" >}}

##### Step 3: Declare the headers to be modified

Select the headers to delete and insert using the provided fields. You need to click **ADD** to ensure they are added to the list.

{{< img src="/img/dashboard/endpoint-designer/response-header-details.png" alt="Configuring the response header transform" >}}

##### Step 4: Save the API

Use the *save* or *create* buttons to save the changes and activate the middleware.

## Configuring the Response Header Transform in Tyk Operator {#tyk-operator}

The process for configuring a response header transform in Tyk Operator is similar to that defined in section [configuring the Response Header Transform in the Tyk Classic API Definition](#tyk-classic). Tyk Operator allows you to configure a response header transformation for [all endpoints of an API](#tyk-operator-endpoint) or for a [specific API endpoint](#tyk-operator-api).

### API-level transform {#tyk-operator-api}

The process of configuring transformation of response headers for a specific API in Tyk Operator is similar to that defined in section [API-level transform](#tyk-classic-api) for the Tyk Classic API definition. 

To **append** headers to all responses from your API (i.e. for all endpoints) you must add a new `global_response_headers` object to the `versions` section of your API definition. This contains a list of key:value pairs, being the names and values of the headers to be added to responses.

To **delete** headers from all responses from your API (i.e. for all endpoints), you must add a new `global_response_headers_remove` object to the `versions` section of the API definition. This contains a list of the names of existing headers to be removed from responses.

An example is listed below:

```yaml {linenos=true, linenostart=1, hl_lines=["25-30"]}
apiVersion: tyk.tyk.io/v1alpha1
kind: ApiDefinition
metadata:
  name: httpbin-global-header
spec:
  name: httpbin-global-header
  use_keyless: true
  protocol: http
  active: true
  proxy:
    target_url: http://httpbin.org
    listen_path: /httpbin-global-header
    strip_listen_path: true
  version_data:
    default_version: Default
    not_versioned: true
    versions:
      Default:
        name: Default
        use_extended_paths: true
        paths:
          black_list: []
          ignored: []
          white_list: []
        global_response_headers:
          X-Static: foobar
          X-Request-ID: "$tyk_context.request_id"
          X-User-ID: "$tyk_meta.uid"
        global_response_headers_remove:
          - X-Secret
```

The example API Definition above configures an API to listen on path `/httpbin-global-header` and forwards requests upstream to http://httpbin.org.

This configuration will add three new headers to each response:

- `X-Static` with the value `foobar`
- `X-Request-ID` with a dynamic value taken from the `request_id` [context variable]({{< ref "context-variables" >}})
- `X-User-ID` with a dynamic value taken from the `uid` field in the [session metadata]({{< ref "getting-started/key-concepts/session-meta-data" >}})

It will also delete one header (if present) from each response:

- `X-Secret`


### Endpoint-level transform {#tyk-operator-endpoint}

The process of configuring a transformation of a response header for a specific endpoint in Tyk Operator is similar to that defined in section [endpoint-level transform](#tyk-classic-endpoint) for the Tyk Classic API definition. To configure a transformation of the response headers for a specific endpoint you must add a new `transform_response_headers` object to the `extended_paths` section of your API definition.

In this example the Response Header Transform middleware (`transform_response_headers`) has been configured for HTTP `GET` requests to the `/xml` endpoint. Any response received from the upstream service following a request to that endpoint will have the `Content-Type` header added with a value set to `application/json`.

##### Example

```yaml {linenos=true, linenostart=1, hl_lines=["54-60"]}
apiVersion: tyk.tyk.io/v1alpha1
kind: ApiDefinition
metadata:
  name: httpbin-transform
spec:
  name: httpbin-transform
  use_keyless: true
  protocol: http
  active: true
  proxy:
    target_url: http://httpbin.org
    listen_path: /httpbin-transform
    strip_listen_path: true
  version_data:
    default_version: Default
    not_versioned: true
    versions:
      Default:
        name: Default
        use_extended_paths: true
        paths:
          black_list: []
          ignored: []
          white_list: []
        extended_paths:
          transform:
            - method: POST
              path: /anything
              template_data:
                enable_session: false
                input_type: json
                template_mode: blob
                # base64 encoded template
                template_source: eyJiYXIiOiAie3suZm9vfX0ifQ==
          transform_headers:
            - delete_headers:
                - "remove_this"
              add_headers:
                foo: bar
              path: /anything
              method: POST
          transform_response:
            - method: GET
              path: /xml
              template_data:
                enable_session: false
                input_type: xml
                template_mode: blob
                # base64 encoded template
                template_source: e3sgLiB8IGpzb25NYXJzaGFsIH19
          transform_response_headers:
            - method: GET
              path: /xml
              add_headers:
                Content-Type: "application/json"
              act_on: false
              delete_headers: []
```

##### Tyk Gateway < 5.3.0 Example

If using Tyk Gateway < v5.3.0 then a `response_processor` object must be added to the API definition containing a `header_injector` item, as highlighted below:

```yaml  {linenos=true, linenostart=1, hl_lines=["17", "19", "57-63"]}
apiVersion: tyk.tyk.io/v1alpha1
kind: ApiDefinition
metadata:
  name: httpbin-transform
spec:
  name: httpbin-transform
  use_keyless: true
  protocol: http
  active: true
  proxy:
    target_url: http://httpbin.org
    listen_path: /httpbin-transform
    strip_listen_path: true
  response_processors:
    - name: response_body_transform
    - name: header_injector
  version_data:
    default_version: Default
    not_versioned: true
    versions:
      Default:
        name: Default
        use_extended_paths: true
        paths:
          black_list: []
          ignored: []
          white_list: []
        extended_paths:
          transform:
            - method: POST
              path: /anything
              template_data:
                enable_session: false
                input_type: json
                template_mode: blob
                # base64 encoded template
                template_source: eyJiYXIiOiAie3suZm9vfX0ifQ==
          transform_headers:
            - delete_headers:
                - "remove_this"
              add_headers:
                foo: bar
              path: /anything
              method: POST
          transform_response:
            - method: GET
              path: /xml
              template_data:
                enable_session: false
                input_type: xml
                template_mode: blob
                # base64 encoded template
                template_source: e3sgLiB8IGpzb25NYXJzaGFsIH19
          transform_response_headers:
            - method: GET
              path: /xml
              add_headers:
                Content-Type: "application/json"
              act_on: false
              delete_headers: []
```
