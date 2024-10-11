---
title: stdout
description: Explains an overview of configuring stdout output
tags: [ "Tyk Streams", "Stream Outputs", "Outputs", "stdout" ]
---

Prints messages to stdout as a continuous stream of data.

```yml
# Config fields, showing default values
output:
  label: ""
  stdout:
    codec: lines
```

## Fields

### codec

The way in which the bytes of messages should be written out into the output data stream. It's possible to write lines using a custom delimiter with the `delim:x` codec, where x is the character sequence custom delimiter.


Type: `string`  
Default: `"lines"`  

| Option | Summary |
|---|---|
| `all-bytes` | Only applicable to file based outputs. Writes each message to a file in full, if the file already exists the old content is deleted. |
| `append` | Append each message to the output stream without any delimiter or special encoding. |
| `lines` | Append each message to the output stream followed by a line break. |
| `delim:x` | Append each message to the output stream followed by a custom delimiter. |


```yml
# Examples

codec: lines

codec: "delim:\t"

codec: delim:foobar
```