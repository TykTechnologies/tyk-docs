---
title: NSQ
description: Explains the input type NSQ, a real-time distributed messaging platform
tags: [ "Tyk Streams NSQ", "Stream Inputs NSQ", "Inputs NSQ", "NSQ" ]
---

Subscribe to an [NSQ](https://nsq.io/) instance topic and channel.


## Common config fields
Showing common config fields and default values

```yml
input:
  label: ""
  nsq:
    nsqd_tcp_addresses: [] # No default (required)
    lookupd_http_addresses: [] # No default (required)
    topic: "" # No default (required)
    channel: "" # No default (required)
    user_agent: "" # No default (optional)
    max_in_flight: 100
    max_attempts: 5
```

## Advanced config fields
Showing all config fields and default values

```yml
input:
  label: ""
  nsq:
    nsqd_tcp_addresses: [] # No default (required)
    lookupd_http_addresses: [] # No default (required)
    tls:
      enabled: false
      skip_cert_verify: false
      enable_renegotiation: false
      root_cas: ""
      root_cas_file: ""
      client_certs: []
    topic: "" # No default (required)
    channel: "" # No default (required)
    user_agent: "" # No default (optional)
    max_in_flight: 100
    max_attempts: 5
```

### Metadata

This input adds the following metadata fields to each message:

```text
- nsq_attempts
- nsq_id
- nsq_nsqd_address
- nsq_timestamp
```

You can access these metadata fields using [function interpolation]({{< ref "/product-stack/tyk-streaming/configuration/common-configuration/interpolation#bloblang-queries" >}}).


## Fields

### nsqd_tcp_addresses

A list of [nsqd daemon](https://nsq.io/components/nsqd.html) addresses to connect to.


Type: `array`  

### lookupd_http_addresses

A list of nsqlookupd addresses to connect to.


Type: `array`  

### tls

Custom TLS settings can be used to override system defaults.


Type: `object`  

### tls.enabled

Whether custom TLS settings are enabled.


Type: `bool`  
Default: `false`  

### tls.skip_cert_verify

Whether to skip server side certificate verification.


Type: `bool`  
Default: `false`  

### tls.enable_renegotiation

Whether to allow the remote server to repeatedly request renegotiation. Enable this option if you're seeing the error message `local error: tls: no renegotiation`.


Type: `bool`  
Default: `false`  
Requires version 3.45.0 or newer  

### tls.root_cas

An optional root certificate authority to use. This is a string, representing a certificate chain from the parent trusted root certificate, to possible intermediate signing certificates, to the host certificate.

Type: `string`  
Default: `""`  

```yml
# Examples

root_cas: |-
  -----BEGIN CERTIFICATE-----
  ...
  -----END CERTIFICATE-----
```

### tls.root_cas_file

An optional path of a root certificate authority file to use. This is a file, often with a .pem extension, containing a certificate chain from the parent trusted root certificate, to possible intermediate signing certificates, to the host certificate.


Type: `string`  
Default: `""`  

```yml
# Examples

root_cas_file: ./root_cas.pem
```

### tls.client_certs

A list of client certificates to use. For each certificate either the fields `cert` and `key`, or `cert_file` and `key_file` should be specified, but not both.


Type: `array`  
Default: `[]`  

```yml
# Examples

client_certs:
  - cert: foo
    key: bar

client_certs:
  - cert_file: ./example.pem
    key_file: ./example.key
```

### tls.client_certs[].cert

A plain text certificate to use.


Type: `string`  
Default: `""`  

### tls.client_certs[].key

A plain text certificate key to use.


Type: `string`  
Default: `""`  

### tls.client_certs[].cert_file

The path of a certificate to use.


Type: `string`  
Default: `""`  

### tls.client_certs[].key_file

The path of a certificate key to use.


Type: `string`  
Default: `""`  

### tls.client_certs[].password

A plain text password for when the private key is password encrypted in PKCS#1 or PKCS#8 format. The obsolete `pbeWithMD5AndDES-CBC` algorithm is not supported for the PKCS#8 format. Warning: Since it does not authenticate the ciphertext, it is vulnerable to padding oracle attacks that can let an attacker recover the plaintext.


Type: `string`  
Default: `""`  

```yml
# Example

password: foo
```

<!-- When Tyk streams with secrets released include this in above example => password: ${KEY_PASSWORD} -->

### topic

The topic to consume from.


Type: `string`  

### channel

The channel to consume from.


Type: `string`  

### user_agent

A user agent to assume when connecting.


Type: `string`  

### max_in_flight

The maximum number of pending messages to consume at any given time.


Type: `int`  
Default: `100`  

### max_attempts

The maximum number of attempts to successfully consume a messages.


Type: `int`  
Default: `5`  
