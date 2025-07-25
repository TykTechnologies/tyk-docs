---
date: 2024-11-19T10:10:33Z
title: "Streams"
tags: [ "streaming", "events", "event-driven architecture", "event-driven architectures", "kafka" ]
description: "How to publish Tyk Streams APIs to your Tyk Developer Portal"
menu:
  main:
    parent: "Tyk Portal Classic"
weight: 12
aliases:
  - /tyk-developer-portal/streams
robots: "noindex"
algolia:
  importance: 0
---

{{< include "legacy-classic-portal-api" >}}

As of Tyk v5.7.0, you can now publish Tyk Streams APIs to the Tyk Developer Portal.

## How To Set Up

Simply create a [Tyk Streams API]({{< ref "api-management/event-driven-apis#getting-started" >}}), create a [Policy]({{< ref "api-management/gateway-config-managing-classic#create-a-security-policy-with-the-dashboard" >}}) which protects it, and then [publish it to the Developer Portal Catalog]({{< ref "portal/overview/getting-started#publish-an-api-product" >}}).