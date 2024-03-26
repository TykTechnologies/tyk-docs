---
description: Step by Step guide to setup data to Elasticsearch 8+ in the cloud via Tyk Pump and Fluent-bit
title: Elasticsearch 8+ Setup via Fluent-bit
tags: ["Tyk Pump", "Configuration", "Elasticsearch 8"]
---

This is a step by step guide to configure in Kubernetes how to send data from Tyk Stack to Elasticsearch.

We will be using Tyk Pump configured to send the data to stdout and then using Fluent-bit to send the data to Elasticsearch 8+

Prerequisites

Having Tyk installed, this can be using the Tyk Stack Helm Chart.


Configure Tyk Pump

Configure Tyk Pump to send data to stdout you can configure the environment variables detailed in this document that includes stdout. 

In this example we will be configuring the basic ones: 

pumps.stdout.name: The name of the pump. This is used to identify the pump in the logs. Deprecated, use type instead.

pumps.stdout.type: Sets the pump type.

In our example we are adding the extra environmental values to the value.yaml from the Tyk Stack Helm Chart. 

To get the file you can use this command:

helm show values tyk-helm/tyk-stack > values.yaml
Update the local values.yaml file with the below variables.
pump:
…..
   extraEnvs:
      - name: TYK_PMP_PUMPS_STDOUT_NAME 
        value: stdout
      - name: TYK_PMP_PUMPS_STDOUT_TYPE
        value: stdout

Upgrade the Tyk Stack Helm Chart you using the following command:


helm upgrade tyk tyk-helm/tyk-stack -f values.yaml


Configure Fluent-bit

Configure Fluent-bit to send data collected from the stdout log to Elasticsearch 8 using the Fluent-bit Helm Chart

You are going to need the Cloud ID from your Elastic Cloud and your Authorization Token. 

To get the Cloud ID:
Access to Elastic Cloud and click on “Manage this deployment”

Click on your deployment and you will see your Cloud ID


To get the Authorization Token, this is something that you should have when deploying your deployment but you can reset it in the security settings from your deployment:
To reset your password you can click on “Reset password”


To install Fluent-Bit

Add the repo:

helm repo add fluent https://fluent.github.io/helm-charts

Get the values.yaml file you can use this command:

helm show values fluent/fluent-bit  > values.yaml


Edit the value.yaml from the Fluent-bit Helm Chart with the following:

Local values.yml services, inputs, services and outputs:

config:
…..
  inputs: |
    [INPUT]
        Name tail
        Path /var/log/containers/*pump*.log
        multiline.parser docker, cri
        Tag kube.*
        Mem_Buf_Limit 5MB
        Skip_Long_Lines On
…..
  outputs: |
    [OUTPUT]
        Name es
        Include_Tag_Key true
        Tag_Key tags
        tls On
        tls.verify Off
        Suppress_Type_Name On
        cloud_id otel:{{ ADD CLOUD_ID}}
        cloud_auth elastic:{{ ADD AUTH TOKEN}}
        Match *

To provide access to the logs to Fluent-bit, change this variable:
securityContext:
  runAsUser: 0

Upgrade the Tyk Stack Helm Chart you using the following command:


helm install fluent-bit fluent/fluent-bit -f values.yaml

Look for the data in Elasticsearch

The data should be now flowing to Elasticsearch, to have a look at that data:

Click on “Indices” and look for “Fluent-bit”






Click in Documents to start seeing logs from the blogs.



