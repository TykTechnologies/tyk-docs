---
title: "API Versioning (Tyk Classic API)"
date: 2024-06-25
tags: ["Tyk", "Kubernetes", "API Management", "CRD", "DevOps", "API Gateway Configuration"]
description: "This documentation provides a comprehensive guide on configuring API versioning within the ApiDefinition Custom Resource Definition (CRD)."
keywords: ["Tyk Operator", "Kubernetes", "API Versioning"]
---

Here is an example custom resource that configure API versioning for Tyk Classic API, mirroring the examples at [API versions]({{<ref "getting-started/key-concepts/versioning">}}) page.

Please consult [API versions]({{<ref "getting-started/key-concepts/versioning">}}) page to understand Tyk Classic API versioning concept and [Set up versioning via the API Definition]({{<ref "getting-started/key-concepts/versioning#set-up-versioning-via-the-api-definition">}}) for a comprehensive guide on fields that enable versioning.

```yaml
apiVersion: tyk.tyk.io/v1alpha1
kind: ApiDefinition
metadata:
  name: versioned-api
spec:
  name: Versioned API
  use_keyless: true
  protocol: http
  active: true
  proxy:
    target_url: http://version-api.example.com
    listen_path: /version-api
    strip_listen_path: true
  definition:
  # Tyk should find version data in Header
    location: header
    key: x-api-version

  # Tyk should find version data in First URL Element
    #location: url

  # Tyk should find version data in URL/Form Parameter
    #location: url-param
    #key: api-version
  version_data:
    default_version: v1
    not_versioned: false
    versions:
      v1:
        name: v1
        expires: ""
        override_target: "http://test.org"
        use_extended_paths: true
        extended_paths:
          ignored:
            - path: /v1/ignored/noregex
              method_actions:
                GET:
                  action: no_action
                  code: 200
                  data: ""
                  headers:
                    x-tyk-override-test: tyk-override
                    x-tyk-override-test-2: tyk-override-2
          white_list:
            - path: v1/allowed/allowlist/literal
              method_actions:
                GET:
                  action: no_action
                  code: 200
                  data: ""
                  headers:
                    x-tyk-override-test: tyk-override
                    x-tyk-override-test-2: tyk-override-2
            - path: v1/allowed/allowlist/reply/{id}
              method_actions:
                GET:
                  action: reply
                  code: 200
                  data: flump
                  headers:
                    x-tyk-override-test: tyk-override
                    x-tyk-override-test-2: tyk-override-2
            - path: v1/allowed/allowlist/{id}
              method_actions:
                GET:
                  action: no_action
                  code: 200
                  data: ""
                  headers:
                    x-tyk-override-test: tyk-override
                    x-tyk-override-test-2: tyk-override-2
          black_list:
            - path: v1/disallowed/blocklist/literal
              method_actions:
                GET:
                  action: no_action
                  code: 200
                  data: ""
                  headers:
                    x-tyk-override-test: tyk-override
                    x-tyk-override-test-2: tyk-override-2
```