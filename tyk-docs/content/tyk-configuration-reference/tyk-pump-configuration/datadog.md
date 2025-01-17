---
title: "Datadog Setup"
date: 2021-10-20
tags: ["Pump", "Datadog", "DogstatsD"]
description: "How configure the Tyk Pump with Datadog"
menu:
    main:
        parent: "Tyk Pump Configuration"
weight: 5 
---

## Introduction

The Tyk Pump can be configured to send your API traffic analytics to [Datadog](https://www.datadoghq.com/) with which you can build a [dashboards](https://docs.datadoghq.com/integrations/tyk/#dashboards) with various metrics based on your API traffic in Tyk.

### Datadog dashboard example

We ceated a defaulkt Tyk dashboard canvat to give our users an easier starting point. You can find it in Datadog portal, under the `Dashboards --> lists` section, (https://app.datadoghq.com/dashboard/lists)[https://app.datadoghq.com/dashboard/lists], and it is called `Tyk Analytics Canvas`. To use this dashboard you will need to make sure that your datadog agent deployment has the following tag `env:tyk-demo-env` and that your Tyk Pump configuration has `dogstatsd.meta.namespace` set to `pump`. You can also import it from [Datadog official GH repo](https://github.com/DataDog/integrations-extras/blob/master/tyk/assets/dashboards/tyk_analytics_canvas.json) and change those values in the dashboard itself to visualize your analytics data as it flows into Datadog.

{{< img src="/img/pump/datadog-tyk-analytics-dashboard.jpeg" alt="Sample Datadog dashboard" >}}


## Prerequisites

- A working Datadog agent installed on your Environment. See the [Datadog Tyk integration docs](https://docs.datadoghq.com/integrations/tyk/) for more information.
- Either a [Tyk Pro install]({{< ref "tyk-self-managed#installation-options-for-tyk-self-managed" >}}) or [Tyk OSS Gateway install]({{< ref "tyk-open-source#installation-options-for-tyk-gateway" >}}) along with a [Tyk Pump]({{< ref "tyk-pump.md" >}}) install.

## How it works

When running the Datadog Agent, [DogstatsD](https://github.com/TykTechnologies/tyk-pump#dogstatsd) gets the [request_time](https://docs.datadoghq.com/integrations/tyk/#data-collected) metric from your Tyk Pump in real time, per request, so you can understand the usage of your APIs and get the flexibility of aggregating by various parameters such as date, version, returned code, method etc.

## Tyk Pump configuration

Below is a sample DogstatD section from a Tyk `pump.conf` file

```json
"dogstatsd": {
  "type": "dogstatsd",
  "meta": {
    "address": "dd-agent:8126",
    "namespace": "tyk",
    "async_uds": true,
    "async_uds_write_timeout_seconds": 2,
    "buffered": true,
    "buffered_max_messages": 32,
    "sample_rate": 0.9999999999,
    "tags": [
      "method",
      "response_code",
      "api_version",
      "api_name",
      "api_id",
      "org_id",
      "tracked",
      "path",
      "oauth_id"
    ]
  }
},
```

### Field descriptions

- `address`: address of the datadog agent including host & port
- `namespace`: prefix for your metrics to datadog
- `async_uds`: Enable async [UDS over UDP](https://github.com/Datadog/datadog-go#unix-domain-sockets-client)
- `async_uds_write_timeout_seconds`: Integer write timeout in seconds if `async_uds: true`
- `buffered`: Enable buffering of messages
- `buffered_max_messages`: Max messages in single datagram if `buffered: true`. Default 16
- `sample_rate`: default 1 which equates to 100% of requests. To sample at 50%, set to 0.5
- `tags`: List of tags to be added to the metric. The possible options are listed in the below example

If no tag is specified the fallback behavior is to use the below tags:
- `path`
- `method`
- `response_code`
- `api_version`
- `api_name`
- `api_id`
- `org_id`
- `tracked`
- `oauth_id`

Note that this configuration can generate significant data due to the unbound nature of the `path` tag.


On startup, you should see the loaded configs when initialising the DogstatsD pump
```console
[May 10 15:23:44]  INFO dogstatsd: initializing pump
[May 10 15:23:44]  INFO dogstatsd: namespace: pump.
[May 10 15:23:44]  INFO dogstatsd: sample_rate: 50%
[May 10 15:23:44]  INFO dogstatsd: buffered: true, max_messages: 32
[May 10 15:23:44]  INFO dogstatsd: async_uds: true, write_timeout: 2s
```
