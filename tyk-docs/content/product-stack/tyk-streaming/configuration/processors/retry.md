---
title: Retry
description: Explains an overview of retry processor
tags: [ "Tyk Streams", "Stream Processors", "Processors", "Retry" ]
---

Attempts to execute a series of child processors until success.

```yml
# Config fields, showing default values
label: ""
retry:
  backoff:
    initial_interval: 500ms
    max_interval: 10s
    max_elapsed_time: 1m
  processors: [] # No default (required)
  parallel: false
```

Executes child processors and if a resulting message is errored then, after a specified backoff period, the same original message will be attempted again through those same processors. If the child processors result in more than one message then the retry mechanism will kick in if *any* of the resulting messages are errored.

It is important to note that any mutations performed on the message during these child processors will be discarded for the next retry, and therefore it is safe to assume that each execution of the child processors will always be performed on the data as it was when it first reached the retry processor.

By default the retry backoff has a specified [max_elapsed_time](#backoffmax_elapsed_time), if this time period is reached during retries and an error still occurs these errored messages will proceed through to the next processor after the retry (or your outputs). 

<!-- Normal [error handling patterns](add) can be used on these messages. Dependent on Blpblang query PR -->

In order to avoid permanent loops any error associated with messages as they first enter a retry processor will be cleared.

## Examples

### Retry

This example generates random data items to a server via HTTP. The server can sometimes fail. However, the retry processor can be used to specify a back off policy that will ensure that for each data item the HTTP processor is attempted until either it succeeds or the Tyk Streams instance is stopped.

Furthermore, the maximum elapsed time field can be zeroed-out, which means that for each data item Tyk Streams wait indefinitely until it is sent. This may be done to ensure that the server receives every single data item.

```yaml
input:
  generate:
    interval: 1s
    mapping: 'root.noise = [ "woof", "meow", "moo", "quack" ].index(random_int(min: 0, max: 3))'

pipeline:
  processors:
    - retry:
        backoff:
          initial_interval: 100ms
          max_interval: 5s
          max_elapsed_time: 0s
        processors:
          - http:
              url: 'http://example.com/try/the/server'
              verb: POST

output:
  # Drop everything because it's test data
  drop: {}
```

## Fields

### backoff

Determine time intervals and cut offs for retry attempts.

Type: `object`


### backoff.initial_interval

The initial period to wait between retry attempts.

Type: `string`  
Default: `"500ms"`  

```yml
# Examples

initial_interval: 50ms

initial_interval: 1s
```

### backoff.max_interval

The maximum period to wait between retry attempts

Type: `string`  
Default: `"10s"`  

```yml
# Examples

max_interval: 5s

max_interval: 1m
```

### backoff.max_elapsed_time

The maximum overall period of time to spend on retry attempts before the request is aborted. Setting this value to a zeroed duration (such as `0s`) will result in unbounded retries.

Type: `string`  
Default: `"1m"`  

```yml
# Examples

max_elapsed_time: 1m

max_elapsed_time: 1h
```

### processors

A list of processors to execute on each message.

Type: `array`  

### parallel

When processing batches of messages these batches are ignored and the processors apply to each message sequentially. However, when this field is set to `true` each message will be processed in parallel. Caution should be made to ensure that batch sizes do not surpass a point where this would cause resource (CPU, memory, API limits) contention.


Type: `bool`  
Default: `false`  

## Batching

When messages are batched the child processors of a retry are executed for each individual message in isolation, performed serially by default but in parallel when the field [parallel](#parallel) is set to `true`. This is an intentional limitation of the retry processor and is done in order to ensure that errors are correctly associated with a given input message. Otherwise, the archiving, expansion, grouping, filtering and so on of the child processors could obfuscate this relationship.

<!-- Commented Archive & Unarchiving not in list of supported processors -->

<!-- If the target behavior of your retried processors is "batch aware", in that you wish to perform some processing across the entire batch of messages and repeat it in the event of errors, you can use an [archive processor](/docs/components/processors/archive) to collapse the batch into an individual message. Then, within these child processors either perform your batch aware processing on the archive, or use an [unarchive processor](/docs/components/processors/unarchive) in order to expand the single message back out into a batch.

For example, if the retry processor were being used to wrap an HTTP request where the payload data is a batch archived into a JSON array it should look something like this:

```yaml
pipeline:
  processors:
    - archive:
        format: json_array
    - retry:
        processors:
          - http:
              url: example.com/nope
              verb: POST
    - unarchive:
        format: json_array
``` -->
