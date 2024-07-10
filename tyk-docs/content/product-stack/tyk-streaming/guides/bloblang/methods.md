---
title: Bloblang Methods
description: Explains Bloblang Methods
tags: [ "Tyk Streams", "Bloblang", "Bloblang Methods", "Methods" ]
---

Methods provide most of the power in [Bloblang]({< ref "/product-stack/tyk-streaming/guides/bloblang/overview" >}) as they allow you to augment values and can be added to any expression (including other methods):

```coffee
root.doc.id = this.thing.id.string().catch(uuid_v4())
root.doc.reduced_nums = this.thing.nums.map_each(num -> if num < 10 {
  deleted()
} else {
  num - 10
})
root.has_good_taste = ["pikachu","mewtwo","magmar"].contains(this.user.fav_pokemon)
```

Methods support both named and nameless style arguments:

```coffee
root.foo_one = this.(bar | baz).trim().replace_all(old: "dog", new: "cat")
root.foo_two = this.(bar | baz).trim().replace_all("dog", "cat")
```

## General

### apply

Apply a declared mapping to a target value.

#### Parameters

**mapping** &lt;string&gt; The mapping to apply.  

#### Examples


```coffee
map thing {
  root.inner = this.first
}

root.foo = this.doc.apply("thing")

# In:  {"doc":{"first":"hello world"}}
# Out: {"foo":{"inner":"hello world"}}
```

```coffee
map create_foo {
  root.name = "a foo"
  root.purpose = "to be a foo"
}

root = this
root.foo = null.apply("create_foo")

# In:  {"id":"1234"}
# Out: {"foo":{"name":"a foo","purpose":"to be a foo"},"id":"1234"}
```

### catch

If the result of a target query fails (due to incorrect types, failed parsing, etc) the argument is returned instead.

#### Parameters

**fallback** &lt;query expression&gt; A value to yield, or query to execute, if the target query fails.  

#### Examples


```coffee
root.doc.id = this.thing.id.string().catch(uuid_v4())
```

The fallback argument can be a mapping, allowing you to capture the error string and yield structured data back.

```coffee
root.url = this.url.parse_url().catch(err -> {"error":err,"input":this.url})

# In:  {"url":"invalid %&# url"}
# Out: {"url":{"error":"field `this.url`: parse \"invalid %&\": invalid URL escape \"%&\"","input":"invalid %&# url"}}
```

When the input document is not structured attempting to reference structured fields with `this` will result in an error. Therefore, a convenient way to delete non-structured data is with a catch.

```coffee
root = this.catch(deleted())

# In:  {"doc":{"foo":"bar"}}
# Out: {"doc":{"foo":"bar"}}

# In:  not structured data
# Out: <Message deleted>
```

### exists

Checks that a field, identified via a [dot path]({{< ref "/product-stack/tyk-streaming/configuration/common-configuration/field-paths" >}}), exists in an object.

#### Parameters

**path** &lt;string&gt; A [dot path]({{< ref "/product-stack/tyk-streaming/configuration/common-configuration/field-paths" >}}) to a field.  

#### Examples

```coffee
root.result = this.foo.exists("bar.baz")

# In:  {"foo":{"bar":{"baz":"yep, I exist"}}}
# Out: {"result":true}

# In:  {"foo":{"bar":{}}}
# Out: {"result":false}

# In:  {"foo":{}}
# Out: {"result":false}
```

### from

Modifies a target query such that certain functions are executed from the perspective of another message in the batch. This allows you to mutate events based on the contents of other messages. Functions that support this behavior are `content`, `json` and `meta`.

#### Parameters

**index** &lt;integer&gt; The message index to use as a perspective.  

#### Examples


For example, the following map extracts the contents of the JSON field `foo` specifically from message index `1` of a batch, effectively overriding the field `foo` for all messages of a batch to that of message 1:

```coffee
root = this
root.foo = json("foo").from(1)
```

### from_all

Modifies a target query such that certain functions are executed from the perspective of each message in the batch, and returns the set of results as an array. Functions that support this behavior are `content`, `json` and `meta`.

#### Examples

```coffee
root = this
root.foo_summed = json("foo").from_all().sum()
```

### or

If the result of the target query fails or resolves to `null`, returns the argument instead. This is an explicit method alternative to the coalesce pipe operator `|`.

#### Parameters

**fallback** &lt;query expression&gt; A value to yield, or query to execute, if the target query fails or resolves to `null`.  

#### Examples

```coffee
root.doc.id = this.thing.id.or(uuid_v4())
```

## String Manipulation

### capitalize

Takes a string value and returns a copy with all Unicode letters that begin words mapped to their Unicode title case.

#### Examples


```coffee
root.title = this.title.capitalize()

# In:  {"title":"the foo bar"}
# Out: {"title":"The Foo Bar"}
```

### compare_argon2

Checks whether a string matches a hashed secret using Argon2.

#### Parameters

**hashed_secret** &lt;string&gt; The hashed secret to compare with the input. This must be a fully-qualified string which encodes the Argon2 options used to generate the hash.  

#### Examples


```coffee
root.match = this.secret.compare_argon2("$argon2id$v=19$m=4096,t=3,p=1$c2FsdHktbWNzYWx0ZmFjZQ$RMUMwgtS32/mbszd+ke4o4Ej1jFpYiUqY6MHWa69X7Y")

# In:  {"secret":"there-are-many-blobs-in-the-sea"}
# Out: {"match":true}
```

```coffee
root.match = this.secret.compare_argon2("$argon2id$v=19$m=4096,t=3,p=1$c2FsdHktbWNzYWx0ZmFjZQ$RMUMwgtS32/mbszd+ke4o4Ej1jFpYiUqY6MHWa69X7Y")

# In:  {"secret":"will-i-ever-find-love"}
# Out: {"match":false}
```

### compare_bcrypt

Checks whether a string matches a hashed secret using bcrypt.

#### Parameters

**hashed_secret** &lt;string&gt; The hashed secret value to compare with the input.  

#### Examples

```coffee
root.match = this.secret.compare_bcrypt("$2y$10$Dtnt5NNzVtMCOZONT705tOcS8It6krJX8bEjnDJnwxiFKsz1C.3Ay")

# In:  {"secret":"there-are-many-blobs-in-the-sea"}
# Out: {"match":true}
```

```coffee
root.match = this.secret.compare_bcrypt("$2y$10$Dtnt5NNzVtMCOZONT705tOcS8It6krJX8bEjnDJnwxiFKsz1C.3Ay")

# In:  {"secret":"will-i-ever-find-love"}
# Out: {"match":false}
```

### contains

Checks whether a string contains a substring and returns a boolean result.

#### Parameters

**value** &lt;unknown&gt; A value to test against elements of the target.  

#### Examples

```coffee
root.has_foo = this.thing.contains("foo")

# In:  {"thing":"this foo that"}
# Out: {"has_foo":true}

# In:  {"thing":"this bar that"}
# Out: {"has_foo":false}
```

### escape_html

Escapes a string so that special characters like `<` to become `&lt;`. It escapes only five such characters: `<`, `>`, `&`, `'` and `"` so that it can be safely placed within an HTML entity.

#### Examples

```coffee
root.escaped = this.value.escape_html()

# In:  {"value":"foo & bar"}
# Out: {"escaped":"foo &amp; bar"}
```

### escape_url_query

Escapes a string so that it can be safely placed within a URL query.

#### Examples


```coffee
root.escaped = this.value.escape_url_query()

# In:  {"value":"foo & bar"}
# Out: {"escaped":"foo+%26+bar"}
```

### filepath_join

Joins an array of path elements into a single file path. The separator depends on the operating system of the machine.

#### Examples


```coffee
root.path = this.path_elements.filepath_join()

# In:  {"path_elements":["/foo/","bar.txt"]}
# Out: {"path":"/foo/bar.txt"}
```

### filepath_split

Splits a file path immediately following the final Separator, separating it into a directory and file name component returned as a two element array of strings. If there is no Separator in the path, the first element will be empty and the second will contain the path. The separator depends on the operating system of the machine.

#### Examples


```coffee
root.path_sep = this.path.filepath_split()

# In:  {"path":"/foo/bar.txt"}
# Out: {"path_sep":["/foo/","bar.txt"]}

# In:  {"path":"baz.txt"}
# Out: {"path_sep":["","baz.txt"]}
```

### format

Use a value string as a format specifier in order to produce a new string, using any number of provided arguments. Please refer to the Go [fmt package documentation](https://pkg.go.dev/fmt) for the list of valid format verbs.

#### Examples

```coffee
root.foo = "%s(%v): %v".format(this.name, this.age, this.fingers)

# In:  {"name":"lance","age":37,"fingers":13}
# Out: {"foo":"lance(37): 13"}
```

### has_prefix

Checks whether a string has a prefix argument and returns a bool.

#### Parameters

**value** &lt;string&gt; The string to test.  

#### Examples


```coffee
root.t1 = this.v1.has_prefix("foo")
root.t2 = this.v2.has_prefix("foo")

# In:  {"v1":"foobar","v2":"barfoo"}
# Out: {"t1":true,"t2":false}
```

### has_suffix

Checks whether a string has a suffix argument and returns a bool.

#### Parameters

**`value`** &lt;string&gt; The string to test.  

#### Examples


```coffee
root.t1 = this.v1.has_suffix("foo")
root.t2 = this.v2.has_suffix("foo")

# In:  {"v1":"foobar","v2":"barfoo"}
# Out: {"t1":false,"t2":true}
```

### index_of

Returns the starting index of the argument substring in a string target, or `-1` if the target doesn't contain the argument.

#### Parameters

**value** &lt;string&gt; A string to search for.  

#### Examples


```coffee
root.index = this.thing.index_of("bar")

# In:  {"thing":"foobar"}
# Out: {"index":3}
```

```coffee
root.index = content().index_of("meow")

# In:  the cat meowed, the dog woofed
# Out: {"index":8}
```

### length

Returns the length of a string.

#### Examples


```coffee
root.foo_len = this.foo.length()

# In:  {"foo":"hello world"}
# Out: {"foo_len":11}
```

### lowercase

Convert a string value into lowercase.

#### Examples


```coffee
root.foo = this.foo.lowercase()

# In:  {"foo":"HELLO WORLD"}
# Out: {"foo":"hello world"}
```

### quote

Quotes a target string using escape sequences (`\t`, `\n`, `\xFF`, `\u0100`) for control characters and non-printable characters.

#### Examples


```coffee
root.quoted = this.thing.quote()

# In:  {"thing":"foo\nbar"}
# Out: {"quoted":"\"foo\\nbar\""}
```

### replace_all

Replaces all occurrences of the first argument in a target string with the second argument.

#### Parameters

**`old`** &lt;string&gt; A string to match against.  
**`new`** &lt;string&gt; A string to replace with.  

#### Examples


```coffee
root.new_value = this.value.replace_all("foo","dog")

# In:  {"value":"The foo ate my homework"}
# Out: {"new_value":"The dog ate my homework"}
```

### replace_all_many

For each pair of strings in an argument array, replaces all occurrences of the first item of the pair with the second. This is a more compact way of chaining a series of `replace_all` methods.

#### Parameters

**values** &lt;array&gt; An array of values, each even value will be replaced with the following odd value.  

#### Examples


```coffee
root.new_value = this.value.replace_all_many([
  "<b>", "&lt;b&gt;",
  "</b>", "&lt;/b&gt;",
  "<i>", "&lt;i&gt;",
  "</i>", "&lt;/i&gt;",
])

# In:  {"value":"<i>Hello</i> <b>World</b>"}
# Out: {"new_value":"&lt;i&gt;Hello&lt;/i&gt; &lt;b&gt;World&lt;/b&gt;"}
```

### reverse

Returns the target string in reverse order.

#### Examples


```coffee
root.reversed = this.thing.reverse()

# In:  {"thing":"backwards"}
# Out: {"reversed":"sdrawkcab"}
```

```coffee
root = content().reverse()

# In:  {"thing":"backwards"}
# Out: }"sdrawkcab":"gniht"{
```

### slice

Extract a slice from a string by specifying two indices, a low and high bound, which selects a half-open range that includes the first character, but excludes the last one. If the second index is omitted then it defaults to the length of the input sequence.

#### Parameters

**low** &lt;integer&gt; The low bound, which is the first element of the selection, or if negative selects from the end.  
**high** &lt;(optional) integer&gt; An optional high bound.  

#### Examples


```coffee
root.beginning = this.value.slice(0, 2)
root.end = this.value.slice(4)

# In:  {"value":"foo bar"}
# Out: {"beginning":"fo","end":"bar"}
```

A negative low index can be used, indicating an offset from the end of the sequence. If the low index is greater than the length of the sequence then an empty result is returned.

```coffee
root.last_chunk = this.value.slice(-4)
root.the_rest = this.value.slice(0, -4)

# In:  {"value":"foo bar"}
# Out: {"last_chunk":" bar","the_rest":"foo"}
```

### slug

Creates a "slug" from a given string. Wraps the *github.com/gosimple/slug* package. See accompanying [docs](https://pkg.go.dev/github.com/gosimple/slug) for more information.

#### Parameters

**lang** &lt;(optional) string, default `"en"`&gt;   

#### Examples

Creates a slug from an English string

```coffee
root.slug = this.value.slug()

# In:  {"value":"Tyk & Streams"}
# Out: {"slug":"tyk-and-streams"}
```

Creates a slug from a French string

```coffee
root.slug = this.value.slug("fr")

# In:  {"value":"Gaufre & Poisson d'Eau Profonde"}
# Out: {"slug":"gaufre-et-poisson-deau-profonde"}
```

### split

Split a string value into an array of strings by splitting it on a string separator.

#### Parameters

**delimiter** &lt;string&gt; The delimiter to split with.  

#### Examples


```coffee
root.new_value = this.value.split(",")

# In:  {"value":"foo,bar,baz"}
# Out: {"new_value":["foo","bar","baz"]}
```

### strip_html

Attempts to remove all HTML tags from a target string.

#### Parameters

**preserve** &lt;(optional) array&gt; An optional array of element types to preserve in the output.  

#### Examples


```coffee
root.stripped = this.value.strip_html()

# In:  {"value":"<p>the plain <strong>old text</strong></p>"}
# Out: {"stripped":"the plain old text"}
```

It's also possible to provide an explicit list of element types to preserve in the output.

```coffee
root.stripped = this.value.strip_html(["article"])

# In:  {"value":"<article><p>the plain <strong>old text</strong></p></article>"}
# Out: {"stripped":"<article>the plain old text</article>"}
```

### trim

Remove all leading and trailing characters from a string that are contained within an argument cutset. If no arguments are provided then whitespace is removed.

#### Parameters

**cutset** &lt;(optional) string&gt; An optional string of characters to trim from the target value.  

#### Examples


```coffee
root.title = this.title.trim("!?")
root.description = this.description.trim()

# In:  {"description":"  something happened and its amazing! ","title":"!!!watch out!?"}
# Out: {"description":"something happened and its amazing!","title":"watch out"}
```

### trim_prefix

Remove the provided leading prefix substring from a string. If the string does not have the prefix substring, it is returned unchanged.


#### Parameters

**prefix** &lt;string&gt; The leading prefix substring to trim from the string.  

#### Examples


```coffee
root.name = this.name.trim_prefix("foobar_")
root.description = this.description.trim_prefix("foobar_")

# In:  {"description":"unchanged","name":"foobar_blobton"}
# Out: {"description":"unchanged","name":"blobton"}
```

### trim_suffix

Remove the provided trailing suffix substring from a string. If the string does not have the suffix substring, it is returned unchanged.


#### Parameters

**suffix** &lt;string&gt; The trailing suffix substring to trim from the string.  

#### Examples


```coffee
root.name = this.name.trim_suffix("_foobar")
root.description = this.description.trim_suffix("_foobar")

# In:  {"description":"unchanged","name":"blobton_foobar"}
# Out: {"description":"unchanged","name":"blobton"}
```

### unescape_html

Unescapes a string so that entities like `&lt;` become `<`. It unescapes a larger range of entities than `escape_html` escapes. For example, `&aacute;` unescapes to `á`, as does `&#225;` and `&xE1;`.

#### Examples


```coffee
root.unescaped = this.value.unescape_html()

# In:  {"value":"foo &amp; bar"}
# Out: {"unescaped":"foo & bar"}
```

### unescape_url_query

Expands escape sequences from a URL query string.

#### Examples


```coffee
root.unescaped = this.value.unescape_url_query()

# In:  {"value":"foo+%26+bar"}
# Out: {"unescaped":"foo & bar"}
```

### unquote

Unquotes a target string, expanding any escape sequences (`\t`, `\n`, `\xFF`, `\u0100`) for control characters and non-printable characters.

#### Examples


```coffee
root.unquoted = this.thing.unquote()

# In:  {"thing":"\"foo\\nbar\""}
# Out: {"unquoted":"foo\nbar"}
```

### uppercase

Convert a string value into uppercase.

#### Examples


```coffee
root.foo = this.foo.uppercase()

# In:  {"foo":"hello world"}
# Out: {"foo":"HELLO WORLD"}
```

## Regular Expressions

### re_find_all

Returns an array containing all successive matches of a regular expression in a string.

#### Parameters

**pattern** &lt;string&gt; The pattern to match against.  

#### Examples


```coffee
root.matches = this.value.re_find_all("a.")

# In:  {"value":"paranormal"}
# Out: {"matches":["ar","an","al"]}
```

### re_find_all_object

Returns an array of objects containing all matches of the regular expression and the matches of its subexpressions. The key of each match value is the name of the group when specified, otherwise it is the index of the matching group, starting with the expression as a whole at 0.

#### Parameters

**`pattern`** &lt;string&gt; The pattern to match against.  

#### Examples


```coffee
root.matches = this.value.re_find_all_object("a(?P<foo>x*)b")

# In:  {"value":"-axxb-ab-"}
# Out: {"matches":[{"0":"axxb","foo":"xx"},{"0":"ab","foo":""}]}
```

```coffee
root.matches = this.value.re_find_all_object("(?m)(?P<key>\\w+):\\s+(?P<value>\\w+)$")

# In:  {"value":"option1: value1\noption2: value2\noption3: value3"}
# Out: {"matches":[{"0":"option1: value1","key":"option1","value":"value1"},{"0":"option2: value2","key":"option2","value":"value2"},{"0":"option3: value3","key":"option3","value":"value3"}]}
```

### re_find_all_submatch

Returns an array of arrays containing all successive matches of the regular expression in a string and the matches, if any, of its subexpressions.

#### Parameters

**pattern** &lt;string&gt; The pattern to match against.  

#### Examples


```coffee
root.matches = this.value.re_find_all_submatch("a(x*)b")

# In:  {"value":"-axxb-ab-"}
# Out: {"matches":[["axxb","xx"],["ab",""]]}
```

### re_find_object

Returns an object containing the first match of the regular expression and the matches of its subexpressions. The key of each match value is the name of the group when specified, otherwise it is the index of the matching group, starting with the expression as a whole at 0.

#### Parameters

**pattern** &lt;string&gt; The pattern to match against.  

#### Examples


```coffee
root.matches = this.value.re_find_object("a(?P<foo>x*)b")

# In:  {"value":"-axxb-ab-"}
# Out: {"matches":{"0":"axxb","foo":"xx"}}
```

```coffee
root.matches = this.value.re_find_object("(?P<key>\\w+):\\s+(?P<value>\\w+)")

# In:  {"value":"option1: value1"}
# Out: {"matches":{"0":"option1: value1","key":"option1","value":"value1"}}
```

### re_match

Checks whether a regular expression matches against any part of a string and returns a boolean.

#### Parameters

**pattern** &lt;string&gt; The pattern to match against.  

#### Examples


```coffee
root.matches = this.value.re_match("[0-9]")

# In:  {"value":"there are 10 puppies"}
# Out: {"matches":true}

# In:  {"value":"there are ten puppies"}
# Out: {"matches":false}
```

### re_replace_all

Replaces all occurrences of the argument regular expression in a string with a value. Inside the value $ signs are interpreted as submatch expansions, e.g. `$1` represents the text of the first submatch.

#### Parameters

**pattern** &lt;string&gt; The pattern to match against.  
**value** &lt;string&gt; The value to replace with.  

#### Examples


```coffee
root.new_value = this.value.re_replace_all("ADD ([0-9]+)","+($1)")

# In:  {"value":"foo ADD 70"}
# Out: {"new_value":"foo +(70)"}
```

## Number Manipulation

### abs

Returns the absolute value of an int64 or float64 number. As a special case, when an integer is provided that is the minimum value it is converted to the maximum value.

#### Examples


```coffee

root.outs = this.ins.map_each(ele -> ele.abs())


# In:  {"ins":[9,-18,1.23,-4.56]}
# Out: {"outs":[9,18,1.23,4.56]}
```

### ceil

Returns the least integer value greater than or equal to a number. If the resulting value fits within a 64-bit integer then that is returned, otherwise a new floating point number is returned.

#### Examples


```coffee
root.new_value = this.value.ceil()

# In:  {"value":5.3}
# Out: {"new_value":6}

# In:  {"value":-5.9}
# Out: {"new_value":-5}
```

### float32

Converts a numerical type into a 32-bit floating point number, this is for advanced use cases where a specific data type is needed for a given component (such as the ClickHouse SQL driver).

If the value is a string then an attempt will be made to parse it as a 32-bit floating point number. Please refer to the [strconv.ParseFloat documentation](https://pkg.go.dev/strconv#ParseFloat) for details regarding the supported formats.

#### Examples

```coffee

root.out = this.in.float32()


# In:  {"in":"6.674282313423543523453425345e-11"}
# Out: {"out":6.674283e-11}
```

### float64

Converts a numerical type into a 64-bit floating point number, this is for advanced use cases where a specific data type is needed for a given component (such as the ClickHouse SQL driver).

If the value is a string then an attempt will be made to parse it as a 64-bit floating point number. Please refer to the [strconv.ParseFloat documentation](https://pkg.go.dev/strconv#ParseFloat) for details regarding the supported formats.

#### Examples

```coffee

root.out = this.in.float64()


# In:  {"in":"6.674282313423543523453425345e-11"}
# Out: {"out":6.674282313423544e-11}
```

### floor

Returns the greatest integer value less than or equal to the target number. If the resulting value fits within a 64-bit integer then that is returned, otherwise a new floating point number is returned.

#### Examples


```coffee
root.new_value = this.value.floor()

# In:  {"value":5.7}
# Out: {"new_value":5}
```

### int16

Converts a numerical type into a 16-bit signed integer, this is for advanced use cases where a specific data type is needed for a given component (such as the ClickHouse SQL driver).

If the value is a string then an attempt will be made to parse it as a 16-bit signed integer. If the target value exceeds the capacity of an integer or contains decimal values then this method will throw an error. In order to convert a floating point number containing decimals first use [.round()](#round) on the value. Please refer to the [strconv.ParseInt documentation](https://pkg.go.dev/strconv#ParseInt) for details regarding the supported formats.

#### Examples

```coffee

root.a = this.a.int16()
root.b = this.b.round().int16()
root.c = this.c.int16()
root.d = this.d.int16().catch(0)


# In:  {"a":12,"b":12.34,"c":"12","d":-12}
# Out: {"a":12,"b":12,"c":12,"d":-12}
```

```coffee

root = this.int16()


# In:  "0xDE"
# Out: 222
```

### int32

Converts a numerical type into a 32-bit signed integer, this is for advanced use cases where a specific data type is needed for a given component (such as the ClickHouse SQL driver).

If the value is a string then an attempt will be made to parse it as a 32-bit signed integer. If the target value exceeds the capacity of an integer or contains decimal values then this method will throw an error. In order to convert a floating point number containing decimals first use [.round()](#round) on the value. Please refer to the [strconv.ParseInt documentation](https://pkg.go.dev/strconv#ParseInt) for details regarding the supported formats.

#### Examples


```coffee

root.a = this.a.int32()
root.b = this.b.round().int32()
root.c = this.c.int32()
root.d = this.d.int32().catch(0)


# In:  {"a":12,"b":12.34,"c":"12","d":-12}
# Out: {"a":12,"b":12,"c":12,"d":-12}
```

```coffee

root = this.int32()


# In:  "0xDEAD"
# Out: 57005
```

### int64


Converts a numerical type into a 64-bit signed integer, this is for advanced use cases where a specific data type is needed for a given component (such as the ClickHouse SQL driver).

If the value is a string then an attempt will be made to parse it as a 64-bit signed integer. If the target value exceeds the capacity of an integer or contains decimal values then this method will throw an error. In order to convert a floating point number containing decimals first use [.round()](#round) on the value. Please refer to the [strconv.ParseInt documentation](https://pkg.go.dev/strconv#ParseInt) for details regarding the supported formats.

#### Examples


```coffee

root.a = this.a.int64()
root.b = this.b.round().int64()
root.c = this.c.int64()
root.d = this.d.int64().catch(0)


# In:  {"a":12,"b":12.34,"c":"12","d":-12}
# Out: {"a":12,"b":12,"c":12,"d":-12}
```

```coffee

root = this.int64()


# In:  "0xDEADBEEF"
# Out: 3735928559
```

### int8

Converts a numerical type into a 8-bit signed integer, this is for advanced use cases where a specific data type is needed for a given component (such as the ClickHouse SQL driver).

If the value is a string then an attempt will be made to parse it as a 8-bit signed integer. If the target value exceeds the capacity of an integer or contains decimal values then this method will throw an error. In order to convert a floating point number containing decimals first use [.round()](#round) on the value. Please refer to the [strconv.ParseInt documentation](https://pkg.go.dev/strconv#ParseInt) for details regarding the supported formats.

#### Examples

```coffee

root.a = this.a.int8()
root.b = this.b.round().int8()
root.c = this.c.int8()
root.d = this.d.int8().catch(0)


# In:  {"a":12,"b":12.34,"c":"12","d":-12}
# Out: {"a":12,"b":12,"c":12,"d":-12}
```

```coffee

root = this.int8()


# In:  "0xD"
# Out: 13
```

### log

Returns the natural logarithm of a number.

#### Examples

```coffee
root.new_value = this.value.log().round()

# In:  {"value":1}
# Out: {"new_value":0}

# In:  {"value":2.7183}
# Out: {"new_value":1}
```

### log10

Returns the decimal logarithm of a number.

#### Examples


```coffee
root.new_value = this.value.log10()

# In:  {"value":100}
# Out: {"new_value":2}

# In:  {"value":1000}
# Out: {"new_value":3}
```

### max

Returns the largest numerical value found within an array. All values must be numerical and the array must not be empty, otherwise an error is returned.

#### Examples


```coffee
root.biggest = this.values.max()

# In:  {"values":[0,3,2.5,7,5]}
# Out: {"biggest":7}
```

```coffee
root.new_value = [0,this.value].max()

# In:  {"value":-1}
# Out: {"new_value":0}

# In:  {"value":7}
# Out: {"new_value":7}
```

### min

Returns the smallest numerical value found within an array. All values must be numerical and the array must not be empty, otherwise an error is returned.

#### Examples


```coffee
root.smallest = this.values.min()

# In:  {"values":[0,3,-2.5,7,5]}
# Out: {"smallest":-2.5}
```

```coffee
root.new_value = [10,this.value].min()

# In:  {"value":2}
# Out: {"new_value":2}

# In:  {"value":23}
# Out: {"new_value":10}
```

### round

Rounds numbers to the nearest integer, rounding half away from zero. If the resulting value fits within a 64-bit integer then that is returned, otherwise a new floating point number is returned.

#### Examples


```coffee
root.new_value = this.value.round()

# In:  {"value":5.3}
# Out: {"new_value":5}

# In:  {"value":5.9}
# Out: {"new_value":6}
```

### uint16

Converts a numerical type into a 16-bit unsigned integer, this is for advanced use cases where a specific data type is needed for a given component (such as the ClickHouse SQL driver).

If the value is a string then an attempt will be made to parse it as a 16-bit unsigned integer. If the target value exceeds the capacity of an integer or contains decimal values then this method will throw an error. In order to convert a floating point number containing decimals first use [.round()](#round) on the value. Please refer to the [strconv.ParseInt documentation](https://pkg.go.dev/strconv#ParseInt) for details regarding the supported formats.

#### Examples


```coffee

root.a = this.a.uint16()
root.b = this.b.round().uint16()
root.c = this.c.uint16()
root.d = this.d.uint16().catch(0)


# In:  {"a":12,"b":12.34,"c":"12","d":-12}
# Out: {"a":12,"b":12,"c":12,"d":0}
```

```coffee

root = this.uint16()


# In:  "0xDE"
# Out: 222
```

### uint32

Converts a numerical type into a 32-bit unsigned integer, this is for advanced use cases where a specific data type is needed for a given component (such as the ClickHouse SQL driver).

If the value is a string then an attempt will be made to parse it as a 32-bit unsigned integer. If the target value exceeds the capacity of an integer or contains decimal values then this method will throw an error. In order to convert a floating point number containing decimals first use [.round()](#round) on the value. Please refer to the [strconv.ParseInt documentation](https://pkg.go.dev/strconv#ParseInt) for details regarding the supported formats.

#### Examples


```coffee

root.a = this.a.uint32()
root.b = this.b.round().uint32()
root.c = this.c.uint32()
root.d = this.d.uint32().catch(0)


# In:  {"a":12,"b":12.34,"c":"12","d":-12}
# Out: {"a":12,"b":12,"c":12,"d":0}
```

```coffee

root = this.uint32()


# In:  "0xDEAD"
# Out: 57005
```

### uint64

Converts a numerical type into a 64-bit unsigned integer, this is for advanced use cases where a specific data type is needed for a given component (such as the ClickHouse SQL driver).

If the value is a string then an attempt will be made to parse it as a 64-bit unsigned integer. If the target value exceeds the capacity of an integer or contains decimal values then this method will throw an error. In order to convert a floating point number containing decimals first use [.round()](#round) on the value. Please refer to the [strconv.ParseInt documentation](https://pkg.go.dev/strconv#ParseInt) for details regarding the supported formats.

#### Examples

```coffee

root.a = this.a.uint64()
root.b = this.b.round().uint64()
root.c = this.c.uint64()
root.d = this.d.uint64().catch(0)


# In:  {"a":12,"b":12.34,"c":"12","d":-12}
# Out: {"a":12,"b":12,"c":12,"d":0}
```

```coffee

root = this.uint64()


# In:  "0xDEADBEEF"
# Out: 3735928559
```

### uint8

Converts a numerical type into a 8-bit unsigned integer, this is for advanced use cases where a specific data type is needed for a given component (such as the ClickHouse SQL driver).

If the value is a string then an attempt will be made to parse it as a 8-bit unsigned integer. If the target value exceeds the capacity of an integer or contains decimal values then this method will throw an error. In order to convert a floating point number containing decimals first use [.round()](#round) on the value. Please refer to the [strconv.ParseInt documentation](https://pkg.go.dev/strconv#ParseInt) for details regarding the supported formats.

#### Examples

```coffee

root.a = this.a.uint8()
root.b = this.b.round().uint8()
root.c = this.c.uint8()
root.d = this.d.uint8().catch(0)


# In:  {"a":12,"b":12.34,"c":"12","d":-12}
# Out: {"a":12,"b":12,"c":12,"d":0}
```

```coffee

root = this.uint8()


# In:  "0xD"
# Out: 13
```

## Timestamp Manipulation

### parse_duration

Attempts to parse a string as a duration and returns an integer of nanoseconds. A duration string is a possibly signed sequence of decimal numbers, each with an optional fraction and a unit suffix, such as "300ms", "-1.5h" or "2h45m". Valid time units are "ns", "us" (or "µs"), "ms", "s", "m", "h".

#### Examples


```coffee
root.delay_for_ns = this.delay_for.parse_duration()

# In:  {"delay_for":"50us"}
# Out: {"delay_for_ns":50000}
```

```coffee
root.delay_for_s = this.delay_for.parse_duration() / 1000000000

# In:  {"delay_for":"2h"}
# Out: {"delay_for_s":7200}
```

### parse_duration_iso8601

Attempts to parse a string using ISO-8601 rules as a duration and returns an integer of nanoseconds. A duration string is represented by the format "P[n]Y[n]M[n]DT[n]H[n]M[n]S" or "P[n]W". In these representations, the "[n]" is replaced by the value for each of the date and time elements that follow the "[n]". For example, "P3Y6M4DT12H30M5S" represents a duration of "three years, six months, four days, twelve hours, thirty minutes, and five seconds". The last field of the format allows fractions with one decimal place, so "P3.5S" will return 3500000000ns. Any additional decimals will be truncated.

#### Examples


Arbitrary ISO-8601 duration string to nanoseconds:

```coffee
root.delay_for_ns = this.delay_for.parse_duration_iso8601()

# In:  {"delay_for":"P3Y6M4DT12H30M5S"}
# Out: {"delay_for_ns":110839937000000000}
```

Two hours ISO-8601 duration string to seconds:

```coffee
root.delay_for_s = this.delay_for.parse_duration_iso8601() / 1000000000

# In:  {"delay_for":"PT2H"}
# Out: {"delay_for_s":7200}
```

Two and a half seconds ISO-8601 duration string to seconds:

```coffee
root.delay_for_s = this.delay_for.parse_duration_iso8601() / 1000000000

# In:  {"delay_for":"PT2.5S"}
# Out: {"delay_for_s":2.5}
```

### ts_add_iso8601

Parse parameter string as ISO 8601 period and add it to value with high precision for units larger than an hour.

#### Parameters

**duration** &lt;string&gt; Duration in ISO 8601 format  

### ts_format

Attempts to format a timestamp value as a string according to a specified format, or RFC 3339 by default. Timestamp values can either be a numerical unix time in seconds (with up to nanosecond precision via decimals), or a string in RFC 3339 format.

The output format is defined by showing how the reference time, defined to be Mon Jan 2 15:04:05 -0700 MST 2006, would be displayed if it were the value. For an alternative way to specify formats check out the [ts_strftime](#ts_strftime) method.

#### Parameters

**format** &lt;string, default `"2006-01-02T15:04:05.999999999Z07:00"`&gt; The output format to use.  
**tz** &lt;(optional) string&gt; An optional timezone to use, otherwise the timezone of the input string is used, or in the case of unix timestamps the local timezone is used.  

#### Examples

```coffee
root.something_at = (this.created_at + 300).ts_format()
```

An optional string argument can be used in order to specify the output format of the timestamp. The format is defined by showing how the reference time, defined to be Mon Jan 2 15:04:05 -0700 MST 2006, would be displayed if it were the value.

```coffee
root.something_at = (this.created_at + 300).ts_format("2006-Jan-02 15:04:05")
```

A second optional string argument can also be used in order to specify a timezone, otherwise the timezone of the input string is used, or in the case of unix timestamps the local timezone is used.

```coffee
root.something_at = this.created_at.ts_format(format: "2006-Jan-02 15:04:05", tz: "UTC")

# In:  {"created_at":1597405526}
# Out: {"something_at":"2020-Aug-14 11:45:26"}

# In:  {"created_at":"2020-08-14T11:50:26.371Z"}
# Out: {"something_at":"2020-Aug-14 11:50:26"}
```

And `ts_format` supports up to nanosecond precision with floating point timestamp values.

```coffee
root.something_at = this.created_at.ts_format("2006-Jan-02 15:04:05.999999", "UTC")

# In:  {"created_at":1597405526.123456}
# Out: {"something_at":"2020-Aug-14 11:45:26.123456"}

# In:  {"created_at":"2020-08-14T11:50:26.371Z"}
# Out: {"something_at":"2020-Aug-14 11:50:26.371"}
```

### ts_parse

Attempts to parse a string as a timestamp following a specified format and outputs a timestamp, which can then be fed into methods such as [ts_format](#ts_format).

The input format is defined by showing how the reference time, defined to be *Mon Jan 2 15:04:05 -0700 MST 2006*, would be displayed if it were the value. For an alternative way to specify formats check out the [ts_strptime](#ts_strptime) method.

#### Parameters

**format** &lt;string&gt; The format of the target string.  

#### Examples


```coffee
root.doc.timestamp = this.doc.timestamp.ts_parse("2006-Jan-02")

# In:  {"doc":{"timestamp":"2020-Aug-14"}}
# Out: {"doc":{"timestamp":"2020-08-14T00:00:00Z"}}
```

### ts_round

Returns the result of rounding a timestamp to the nearest multiple of the argument duration (nanoseconds). The rounding behavior for halfway values is to round up. Timestamp values can either be a numerical unix time in seconds (with up to nanosecond precision via decimals), or a string in RFC 3339 format. The [ts_parse](#ts_parse) method can be used in order to parse different timestamp formats.


#### Parameters

**duration** &lt;integer&gt; A duration measured in nanoseconds to round by.  

#### Examples


Use the method parse_duration to convert a duration string into an integer argument.

```coffee
root.created_at_hour = this.created_at.ts_round("1h".parse_duration())

# In:  {"created_at":"2020-08-14T05:54:23Z"}
# Out: {"created_at_hour":"2020-08-14T06:00:00Z"}
```

### ts_strftime

Attempts to format a timestamp value as a string according to a specified strftime-compatible format. Timestamp values can either be a numerical unix time in seconds (with up to nanosecond precision via decimals), or a string in RFC 3339 format.

#### Parameters

**format** &lt;string&gt; The output format to use.  
**tz** &lt;(optional) string&gt; An optional timezone to use, otherwise the timezone of the input string is used.  

#### Examples


The format consists of zero or more conversion specifiers and ordinary characters (except `%`). All ordinary characters are copied to the output string without modification. Each conversion specification begins with `%` character followed by the character that determines the behavior of the specifier. Please refer to [man 3 strftime](https://linux.die.net/man/3/strftime) for the list of format specifiers.

```coffee
root.something_at = (this.created_at + 300).ts_strftime("%Y-%b-%d %H:%M:%S")
```

A second optional string argument can also be used in order to specify a timezone, otherwise the timezone of the input string is used, or in the case of unix timestamps the local timezone is used.

```coffee
root.something_at = this.created_at.ts_strftime("%Y-%b-%d %H:%M:%S", "UTC")

# In:  {"created_at":1597405526}
# Out: {"something_at":"2020-Aug-14 11:45:26"}

# In:  {"created_at":"2020-08-14T11:50:26.371Z"}
# Out: {"something_at":"2020-Aug-14 11:50:26"}
```

As an extension provided by the underlying formatting library, [itchyny/timefmt-go](https://github.com/itchyny/timefmt-go), the `%f` directive is supported for zero-padded microseconds, which originates from Python. Note that E and O modifier characters are not supported.

```coffee
root.something_at = this.created_at.ts_strftime("%Y-%b-%d %H:%M:%S.%f", "UTC")

# In:  {"created_at":1597405526}
# Out: {"something_at":"2020-Aug-14 11:45:26.000000"}

# In:  {"created_at":"2020-08-14T11:50:26.371Z"}
# Out: {"something_at":"2020-Aug-14 11:50:26.371000"}
```

### ts_strptime

Attempts to parse a string as a timestamp following a specified strptime-compatible format and outputs a timestamp, which can then be fed into [ts_format](#ts_format).

#### Parameters

**format** &lt;string&gt; The format of the target string.  

#### Examples


The format consists of zero or more conversion specifiers and ordinary characters (except `%`). All ordinary characters are copied to the output string without modification. Each conversion specification begins with a `%` character followed by the character that determines the behavior of the specifier. Please refer to [man 3 strptime](https://linux.die.net/man/3/strptime) for the list of format specifiers.

```coffee
root.doc.timestamp = this.doc.timestamp.ts_strptime("%Y-%b-%d")

# In:  {"doc":{"timestamp":"2020-Aug-14"}}
# Out: {"doc":{"timestamp":"2020-08-14T00:00:00Z"}}
```

As an extension provided by the underlying formatting library, [itchyny/timefmt-go](https://github.com/itchyny/timefmt-go), the `%f` directive is supported for zero-padded microseconds, which originates from Python. Note that E and O modifier characters are not supported.

```coffee
root.doc.timestamp = this.doc.timestamp.ts_strptime("%Y-%b-%d %H:%M:%S.%f")

# In:  {"doc":{"timestamp":"2020-Aug-14 11:50:26.371000"}}
# Out: {"doc":{"timestamp":"2020-08-14T11:50:26.371Z"}}
```

### ts_sub

Returns the difference in nanoseconds between the target timestamp (t1) and the timestamp provided as a parameter (t2). The [ts_parse](#ts_parse) method can be used in order to parse different timestamp formats.

#### Parameters

**t2** &lt;timestamp&gt; The second timestamp to be subtracted from the method target.  

#### Examples

Use the `.abs()` method in order to calculate an absolute duration between two timestamps.

```coffee
root.between = this.started_at.ts_sub("2020-08-14T05:54:23Z").abs()

# In:  {"started_at":"2020-08-13T05:54:23Z"}
# Out: {"between":86400000000000}
```

### ts_sub_iso8601

Parse parameter string as ISO 8601 period and subtract it from value with high precision for units larger than an hour.

#### Parameters

**duration** &lt;string&gt; Duration in ISO 8601 format  

### ts_tz

Returns the result of converting a timestamp to a specified timezone. Timestamp values can either be a numerical unix time in seconds (with up to nanosecond precision via decimals), or a string in RFC 3339 format. The [ts_parse](#ts_parse) method can be used in order to parse different timestamp formats.

#### Parameters

**tz** &lt;string&gt; The timezone to change to. If set to "UTC" then the timezone will be UTC. If set to "Local" then the local timezone will be used. Otherwise, the argument is taken to be a location name corresponding to a file in the IANA Time Zone database, such as "America/New_York".  

#### Examples

```coffee
root.created_at_utc = this.created_at.ts_tz("UTC")

# In:  {"created_at":"2021-02-03T17:05:06+01:00"}
# Out: {"created_at_utc":"2021-02-03T16:05:06Z"}
```

### ts_unix

Attempts to format a timestamp value as a unix timestamp. Timestamp values can either be a numerical unix time in seconds (with up to nanosecond precision via decimals), or a string in RFC 3339 format. The [ts_parse](#ts_parse) method can be used in order to parse different timestamp formats.

#### Examples


```coffee
root.created_at_unix = this.created_at.ts_unix()

# In:  {"created_at":"2009-11-10T23:00:00Z"}
# Out: {"created_at_unix":1257894000}
```

### ts_unix_micro

Attempts to format a timestamp value as a unix timestamp with microsecond precision. Timestamp values can either be a numerical unix time in seconds (with up to nanosecond precision via decimals), or a string in RFC 3339 format. The [ts_parse](#ts_parse) method can be used in order to parse different timestamp formats.

#### Examples


```coffee
root.created_at_unix = this.created_at.ts_unix_micro()

# In:  {"created_at":"2009-11-10T23:00:00Z"}
# Out: {"created_at_unix":1257894000000000}
```

### ts_unix_milli

Attempts to format a timestamp value as a unix timestamp with millisecond precision. Timestamp values can either be a numerical unix time in seconds (with up to nanosecond precision via decimals), or a string in RFC 3339 format. The [ts_parse](#ts_parse) method can be used in order to parse different timestamp formats.

#### Examples


```coffee
root.created_at_unix = this.created_at.ts_unix_milli()

# In:  {"created_at":"2009-11-10T23:00:00Z"}
# Out: {"created_at_unix":1257894000000}
```

### ts_unix_nano

Attempts to format a timestamp value as a unix timestamp with nanosecond precision. Timestamp values can either be a numerical unix time in seconds (with up to nanosecond precision via decimals), or a string in RFC 3339 format. The [ts_parse](#ts_parse) method can be used in order to parse different timestamp formats.

#### Examples


```coffee
root.created_at_unix = this.created_at.ts_unix_nano()

# In:  {"created_at":"2009-11-10T23:00:00Z"}
# Out: {"created_at_unix":1257894000000000000}
```

## Type Coercion

### bool

Attempt to parse a value into a boolean. An optional argument can be provided, in which case if the value cannot be parsed the argument will be returned instead. If the value is a number then any non-zero value will resolve to `true`, if the value is a string then any of the following values are considered valid: `1, t, T, TRUE, true, True, 0, f, F, FALSE`.

#### Parameters

**default** &lt;(optional) bool&gt; An optional value to yield if the target cannot be parsed as a boolean.  

#### Examples

```coffee
root.foo = this.thing.bool()
root.bar = this.thing.bool(true)
```

### bytes

Marshal a value into a byte array. If the value is already a byte array it is unchanged.

#### Examples


```coffee
root.first_byte = this.name.bytes().index(0)

# In:  {"name":"foobar bazson"}
# Out: {"first_byte":102}
```

### not_empty

Ensures that the given string, array or object value is not empty, and if so returns it, otherwise an error is returned.

#### Examples


```coffee
root.a = this.a.not_empty()

# In:  {"a":"foo"}
# Out: {"a":"foo"}

# In:  {"a":""}
# Out: Error("failed assignment (line 1): field `this.a`: string value is empty")

# In:  {"a":["foo","bar"]}
# Out: {"a":["foo","bar"]}

# In:  {"a":[]}
# Out: Error("failed assignment (line 1): field `this.a`: array value is empty")

# In:  {"a":{"b":"foo","c":"bar"}}
# Out: {"a":{"b":"foo","c":"bar"}}

# In:  {"a":{}}
# Out: Error("failed assignment (line 1): field `this.a`: object value is empty")
```

### not_null

Ensures that the given value is not `null`, and if so returns it, otherwise an error is returned.

#### Examples


```coffee
root.a = this.a.not_null()

# In:  {"a":"foobar","b":"barbaz"}
# Out: {"a":"foobar"}

# In:  {"b":"barbaz"}
# Out: Error("failed assignment (line 1): field `this.a`: value is null")
```

### number

Attempt to parse a value into a number. An optional argument can be provided, in which case if the value cannot be parsed into a number the argument will be returned instead.

#### Parameters

**default** &lt;(optional) float&gt; An optional value to yield if the target cannot be parsed as a number.  

#### Examples


```coffee
root.foo = this.thing.number() + 10
root.bar = this.thing.number(5) * 10
```

### string

Marshal a value into a string. If the value is already a string it is unchanged.

#### Examples


```coffee
root.nested_json = this.string()

# In:  {"foo":"bar"}
# Out: {"nested_json":"{\"foo\":\"bar\"}"}
```

```coffee
root.id = this.id.string()

# In:  {"id":228930314431312345}
# Out: {"id":"228930314431312345"}
```

### type

Returns the type of a value as a string, providing one of the following values: `string`, `bytes`, `number`, `bool`, `timestamp`, `array`, `object` or `null`.

#### Examples


```coffee
root.bar_type = this.bar.type()
root.foo_type = this.foo.type()

# In:  {"bar":10,"foo":"is a string"}
# Out: {"bar_type":"number","foo_type":"string"}
```

```coffee
root.type = this.type()

# In:  "foobar"
# Out: {"type":"string"}

# In:  666
# Out: {"type":"number"}

# In:  false
# Out: {"type":"bool"}

# In:  ["foo", "bar"]
# Out: {"type":"array"}

# In:  {"foo": "bar"}
# Out: {"type":"object"}

# In:  null
# Out: {"type":"null"}
```

```coffee
root.type = content().type()

# In:  foobar
# Out: {"type":"bytes"}
```

```coffee
root.type = this.ts_parse("2006-01-02").type()

# In:  "2022-06-06"
# Out: {"type":"timestamp"}
```

## Object & Array Manipulation {#object-array-manipulation}

### all

Checks each element of an array against a query and returns true if all elements passed. An error occurs if the target is not an array, or if any element results in the provided query returning a non-boolean result. Returns false if the target array is empty.

#### Parameters

**test** &lt;query expression&gt; A test query to apply to each element.  

#### Examples


```coffee
root.all_over_21 = this.patrons.all(patron -> patron.age >= 21)

# In:  {"patrons":[{"id":"1","age":18},{"id":"2","age":23}]}
# Out: {"all_over_21":false}

# In:  {"patrons":[{"id":"1","age":45},{"id":"2","age":23}]}
# Out: {"all_over_21":true}
```

### any

Checks the elements of an array against a query and returns true if any element passes. An error occurs if the target is not an array, or if an element results in the provided query returning a non-boolean result. Returns false if the target array is empty.

#### Parameters

**test** &lt;query expression&gt; A test query to apply to each element.  

#### Examples


```coffee
root.any_over_21 = this.patrons.any(patron -> patron.age >= 21)

# In:  {"patrons":[{"id":"1","age":18},{"id":"2","age":23}]}
# Out: {"any_over_21":true}

# In:  {"patrons":[{"id":"1","age":10},{"id":"2","age":12}]}
# Out: {"any_over_21":false}
```

### append

Returns an array with new elements appended to the end.

#### Examples


```coffee
root.foo = this.foo.append("and", "this")

# In:  {"foo":["bar","baz"]}
# Out: {"foo":["bar","baz","and","this"]}
```

### assign

Merge a source object into an existing destination object. When a collision is found within the merged structures (both a source and destination object contain the same non-object keys) the value in the destination object will be overwritten by that of source object. In order to preserve both values on collision use the [merge](#merge) method.

#### Parameters

**with** &lt;unknown&gt; A value to merge the target value with.  

#### Examples


```coffee
root = this.foo.assign(this.bar)

# In:  {"foo":{"first_name":"fooer","likes":"bars"},"bar":{"second_name":"barer","likes":"foos"}}
# Out: {"first_name":"fooer","likes":"foos","second_name":"barer"}
```

### collapse

Collapse an array or object into an object of key/value pairs for each field, where the key is the full path of the structured field in dot path notation. Empty arrays an objects are ignored by default.

#### Parameters

**include_empty** &lt;bool, default `false`&gt; Whether to include empty objects and arrays in the resulting object.  

#### Examples


```coffee
root.result = this.collapse()

# In:  {"foo":[{"bar":"1"},{"bar":{}},{"bar":"2"},{"bar":[]}]}
# Out: {"result":{"foo.0.bar":"1","foo.2.bar":"2"}}
```

An optional boolean parameter can be set to true in order to include empty objects and arrays.

```coffee
root.result = this.collapse(include_empty: true)

# In:  {"foo":[{"bar":"1"},{"bar":{}},{"bar":"2"},{"bar":[]}]}
# Out: {"result":{"foo.0.bar":"1","foo.1.bar":{},"foo.2.bar":"2","foo.3.bar":[]}}
```

### concat

Concatenates an array value with one or more argument arrays.

#### Examples


```coffee
root.foo = this.foo.concat(this.bar, this.baz)

# In:  {"foo":["a","b"],"bar":["c"],"baz":["d","e","f"]}
# Out: {"foo":["a","b","c","d","e","f"]}
```

### contains

Checks whether an array contains an element matching the argument, or an object contains a value matching the argument, and returns a boolean result. Numerical comparisons are made irrespective of the representation type (float versus integer).

#### Parameters

**value** &lt;unknown&gt; A value to test against elements of the target.  

#### Examples


```coffee
root.has_foo = this.thing.contains("foo")

# In:  {"thing":["this","foo","that"]}
# Out: {"has_foo":true}

# In:  {"thing":["this","bar","that"]}
# Out: {"has_foo":false}
```

```coffee
root.has_bar = this.thing.contains(20)

# In:  {"thing":[10.3,20.0,"huh",3]}
# Out: {"has_bar":true}

# In:  {"thing":[2,3,40,67]}
# Out: {"has_bar":false}
```

### diff

Create a diff by comparing the current value with the given one. Wraps the github.com/r3labs/diff/v3 package. See its [docs](https://pkg.go.dev/github.com/r3labs/diff/v3) for more information.

#### Parameters

**other** &lt;unknown&gt; The value to compare against.  

### enumerated

Converts an array into a new array of objects, where each object has a field index containing the `index` of the element and a field `value` containing the original value of the element.

#### Examples


```coffee
root.foo = this.foo.enumerated()

# In:  {"foo":["bar","baz"]}
# Out: {"foo":[{"index":0,"value":"bar"},{"index":1,"value":"baz"}]}
```

### explode

Explodes an array or object at a [field path]({{< ref "/product-stack/tyk-streaming/configuration/common-configuration/field-paths" >}}).

#### Parameters

**path** &lt;string&gt; A [dot path]({{< ref "/product-stack/tyk-streaming/configuration/common-configuration/field-paths" >}}) to a field to explode.  

#### Examples


##### On arrays

Exploding arrays results in an array containing elements matching the original document, where the target field of each element is an element of the exploded array:

```coffee
root = this.explode("value")

# In:  {"id":1,"value":["foo","bar","baz"]}
# Out: [{"id":1,"value":"foo"},{"id":1,"value":"bar"},{"id":1,"value":"baz"}]
```

##### On objects

Exploding objects results in an object where the keys match the target object, and the values match the original document but with the target field replaced by the exploded value:

```coffee
root = this.explode("value")

# In:  {"id":1,"value":{"foo":2,"bar":[3,4],"baz":{"bev":5}}}
# Out: {"bar":{"id":1,"value":[3,4]},"baz":{"id":1,"value":{"bev":5}},"foo":{"id":1,"value":2}}
```

### filter

Executes a mapping query argument for each element of an array or key/value pair of an object. If the query returns `false` the item is removed from the resulting array or object. The item will also be removed if the query returns any non-boolean value.

#### Parameters

**test** &lt;query expression&gt; A query to apply to each element, if this query resolves to any value other than a boolean `true` the element will be removed from the result.  

#### Examples


```coffee
root.new_nums = this.nums.filter(num -> num > 10)

# In:  {"nums":[3,11,4,17]}
# Out: {"new_nums":[11,17]}
```

##### On objects

When filtering objects the mapping query argument is provided a context with a field `key` containing the value key, and a field `value` containing the value.

```coffee
root.new_dict = this.dict.filter(item -> item.value.contains("foo"))

# In:  {"dict":{"first":"hello foo","second":"world","third":"this foo is great"}}
# Out: {"new_dict":{"first":"hello foo","third":"this foo is great"}}
```

### find

Returns the index of the first occurrence of a value in an array. `-1` is returned if there are no matches. Numerical comparisons are made irrespective of the representation type (float versus integer).

#### Parameters

**value** &lt;unknown&gt; A value to find.  

#### Examples


```coffee
root.index = this.find("bar")

# In:  ["foo", "bar", "baz"]
# Out: {"index":1}
```

```coffee
root.index = this.things.find(this.goal)

# In:  {"goal":"bar","things":["foo", "bar", "baz"]}
# Out: {"index":1}
```

### find_all

Returns an array containing the indexes of all occurrences of a value in an array. An empty array is returned if there are no matches. Numerical comparisons are made irrespective of the representation type (float versus integer).

#### Parameters

**value** &lt;unknown&gt; A value to find.  

#### Examples

```coffee
root.index = this.find_all("bar")

# In:  ["foo", "bar", "baz", "bar"]
# Out: {"index":[1,3]}
```

```coffee
root.indexes = this.things.find_all(this.goal)

# In:  {"goal":"bar","things":["foo", "bar", "baz", "bar", "buz"]}
# Out: {"indexes":[1,3]}
```

### find_all_by

Returns an array containing the indexes of all occurrences of an array where the provided query resolves to a boolean `true`. An empty array is returned if there are no matches. Numerical comparisons are made irrespective of the representation type (float versus integer).

#### Parameters

**query** &lt;query expression&gt; A query to execute for each element.  

#### Examples


```coffee
root.index = this.find_all_by(v -> v != "bar")

# In:  ["foo", "bar", "baz"]
# Out: {"index":[0,2]}
```

### find_by

Returns the index of the first occurrence of an array where the provided query resolves to a boolean `true`. `-1` is returned if there are no matches.

#### Parameters

**query** &lt;query expression&gt; A query to execute for each element.  

#### Examples


```coffee
root.index = this.find_by(v -> v != "bar")

# In:  ["foo", "bar", "baz"]
# Out: {"index":0}
```

### flatten

Iterates an array and any element that is itself an array is removed and has its elements inserted directly in the resulting array.

#### Examples


```coffee
root.result = this.flatten()

# In:  ["foo",["bar","baz"],"buz"]
# Out: {"result":["foo","bar","baz","buz"]}
```

### fold

Takes two arguments: an initial value, and a mapping query. For each element of an array the mapping context is an object with two fields `tally` and `value`, where `tally` contains the current accumulated value and `value` is the value of the current element. The mapping must return the result of adding the value to the tally.

The first argument is the value that `tally` will have on the first call.

#### Parameters

**initial** &lt;unknown&gt; The initial value to start the fold with. For example, an empty object `{}`, a zero count `0`, or an empty string `""`.  
**query** &lt;query expression&gt; A query to apply for each element. The query is provided an object with two fields; `tally` containing the current tally, and `value` containing the value of the current element. The query should result in a new tally to be passed to the next element query.  

#### Examples


```coffee
root.sum = this.foo.fold(0, item -> item.tally + item.value)

# In:  {"foo":[3,8,11]}
# Out: {"sum":22}
```

```coffee
root.result = this.foo.fold("", item -> "%v%v".format(item.tally, item.value))

# In:  {"foo":["hello ", "world"]}
# Out: {"result":"hello world"}
```

You can use fold to merge an array of objects together:

```coffee
root.smoothie = this.fruits.fold({}, item -> item.tally.merge(item.value))

# In:  {"fruits":[{"apple":5},{"banana":3},{"orange":8}]}
# Out: {"smoothie":{"apple":5,"banana":3,"orange":8}}
```

### get

Extract a field value, identified via a [dot path]({{< ref "/product-stack/tyk-streaming/configuration/common-configuration/field-paths" >}}), from an object.

#### Parameters

**`path`** &lt;string&gt; A [dot path]({{< ref "/product-stack/tyk-streaming/configuration/common-configuration/field-paths" >}}) identifying a field to obtain.  

#### Examples


```coffee
root.result = this.foo.get(this.target)

# In:  {"foo":{"bar":"from bar","baz":"from baz"},"target":"bar"}
# Out: {"result":"from bar"}

# In:  {"foo":{"bar":"from bar","baz":"from baz"},"target":"baz"}
# Out: {"result":"from baz"}
```

### index

Extract an element from an array by an index. The index can be negative, and if so the element will be selected from the end counting backwards starting from -1. E.g. an index of -1 returns the last element, an index of -2 returns the element before the last, and so on.

#### Parameters

**index** &lt;integer&gt; The index to obtain from an array.  

#### Examples

```coffee
root.last_name = this.names.index(-1)

# In:  {"names":["rachel","stevens"]}
# Out: {"last_name":"stevens"}
```

It is also possible to use this method on byte arrays, in which case the selected element will be returned as an integer.

```coffee
root.last_byte = this.name.bytes().index(-1)

# In:  {"name":"foobar bazson"}
# Out: {"last_byte":110}
```

### join

Join an array of strings with an optional delimiter into a single string.

#### Parameters

**delimiter** &lt;(optional) string&gt; An optional delimiter to add between each string.  

#### Examples


```coffee
root.joined_words = this.words.join()
root.joined_numbers = this.numbers.map_each(this.string()).join(",")

# In:  {"words":["hello","world"],"numbers":[3,8,11]}
# Out: {"joined_numbers":"3,8,11","joined_words":"helloworld"}
```

### json_path

Executes the given [JSONPath expression](https://goessner.net/articles/JsonPath) on an object or array and returns the result. For more complex logic, you can use [Gval expressions](https://github.com/PaesslerAG/gval).

#### Parameters

**expression** &lt;string&gt; The JSONPath expression to execute.  

#### Examples


```coffee
root.all_names = this.json_path("$..name")

# In:  {"name":"alice","foo":{"name":"bob"}}
# Out: {"all_names":["alice","bob"]}

# In:  {"thing":["this","bar",{"name":"alice"}]}
# Out: {"all_names":["alice"]}
```

```coffee
root.text_objects = this.json_path("$.body[?(@.type=='text')]")

# In:  {"body":[{"type":"image","id":"foo"},{"type":"text","id":"bar"}]}
# Out: {"text_objects":[{"id":"bar","type":"text"}]}
```

### json_schema

Checks a [JSON schema](https://json-schema.org/) against a value and returns the value if it matches or throws and error if it does not.

#### Parameters

**schema** &lt;string&gt; The schema to check values against.  

#### Examples


```coffee
root = this.json_schema("""{
  "type":"object",
  "properties":{
    "foo":{
      "type":"string"
    }
  }
}""")

# In:  {"foo":"bar"}
# Out: {"foo":"bar"}

# In:  {"foo":5}
# Out: Error("failed assignment (line 1): field `this`: foo invalid type. expected: string, given: integer")
```

In order to load a schema from a file use the `file` function.

```coffee
root = this.json_schema(file(env("ENV_TEST_BLOBLANG_SCHEMA_FILE")))
```

### key_values

Returns the key/value pairs of an object as an array, where each element is an object with a `key` field and a `value` field. The order of the resulting array will be random.

#### Examples


```coffee
root.foo_key_values = this.foo.key_values().sort_by(pair -> pair.key)

# In:  {"foo":{"bar":1,"baz":2}}
# Out: {"foo_key_values":[{"key":"bar","value":1},{"key":"baz","value":2}]}
```

### keys

Returns the keys of an object as an array.

#### Examples

```coffee
root.foo_keys = this.foo.keys()

# In:  {"foo":{"bar":1,"baz":2}}
# Out: {"foo_keys":["bar","baz"]}
```

### length

Returns the length of an array or object (number of keys).

#### Examples


```coffee
root.foo_len = this.foo.length()

# In:  {"foo":["first","second"]}
# Out: {"foo_len":2}

# In:  {"foo":{"first":"bar","second":"baz"}}
# Out: {"foo_len":2}
```

### map_each

#### Parameters

**query** &lt;query expression&gt; A query that will be used to map each element.  

#### Examples

##### On arrays

Apply a mapping to each element of an array and replace the element with the result. Within the argument mapping the context is the value of the element being mapped.

```coffee
root.new_nums = this.nums.map_each(num -> if num < 10 {
  deleted()
} else {
  num - 10
})

# In:  {"nums":[3,11,4,17]}
# Out: {"new_nums":[1,7]}
```

##### On objects

Apply a mapping to each value of an object and replace the value with the result. Within the argument mapping the context is an object with a field `key` containing the value key, and a field `value`.

```coffee
root.new_dict = this.dict.map_each(item -> item.value.uppercase())

# In:  {"dict":{"foo":"hello","bar":"world"}}
# Out: {"new_dict":{"bar":"WORLD","foo":"HELLO"}}
```

### map_each_key

Apply a mapping to each key of an object, and replace the key with the result, which must be a string.

#### Parameters

**query** &lt;query expression&gt; A query that will be used to map each key.  

#### Examples


```coffee
root.new_dict = this.dict.map_each_key(key -> key.uppercase())

# In:  {"dict":{"keya":"hello","keyb":"world"}}
# Out: {"new_dict":{"KEYA":"hello","KEYB":"world"}}
```

```coffee
root = this.map_each_key(key -> if key.contains("kafka") { "_" + key })

# In:  {"amqp_key":"foo","kafka_key":"bar","kafka_topic":"baz"}
# Out: {"_kafka_key":"bar","_kafka_topic":"baz","amqp_key":"foo"}
```

### merge

Merge a source object into an existing destination object. When a collision is found within the merged structures (both a source and destination object contain the same non-object keys) the result will be an array containing both values, where values that are already arrays will be expanded into the resulting array. In order to simply override destination fields on collision use the [assign](#assign) method.

#### Parameters

**with** &lt;unknown&gt; A value to merge the target value with.  

#### Examples


```coffee
root = this.foo.merge(this.bar)

# In:  {"foo":{"first_name":"fooer","likes":"bars"},"bar":{"second_name":"barer","likes":"foos"}}
# Out: {"first_name":"fooer","likes":["bars","foos"],"second_name":"barer"}
```

### patch

Create a diff by comparing the current value with the given one. Wraps the *github.com/r3labs/diff/v3* package. See its [docs](https://pkg.go.dev/github.com/r3labs/diff/v3) for more information.

#### Parameters

**changelog** &lt;unknown&gt; The changelog to apply.  

### slice

Extract a slice from an array by specifying two indices, a low and high bound, which selects a half-open range that includes the first element, but excludes the last one. If the second index is omitted then it defaults to the length of the input sequence.

#### Parameters

**low** &lt;integer&gt; The low bound, which is the first element of the selection, or if negative selects from the end.  
**high** &lt;(optional) integer&gt; An optional high bound.  

#### Examples


```coffee
root.beginning = this.value.slice(0, 2)
root.end = this.value.slice(4)

# In:  {"value":["foo","bar","baz","buz","bev"]}
# Out: {"beginning":["foo","bar"],"end":["bev"]}
```

A negative low index can be used, indicating an offset from the end of the sequence. If the low index is greater than the length of the sequence then an empty result is returned.

```coffee
root.last_chunk = this.value.slice(-2)
root.the_rest = this.value.slice(0, -2)

# In:  {"value":["foo","bar","baz","buz","bev"]}
# Out: {"last_chunk":["buz","bev"],"the_rest":["foo","bar","baz"]}
```

### sort

Attempts to sort the values of an array in increasing order. The type of all values must match in order for the ordering to succeed. Supports string and number values.

#### Parameters

**compare** &lt;(optional) query expression&gt; An optional query that should explicitly compare elements `left` and `right` and provide a boolean result.  

#### Examples


```coffee
root.sorted = this.foo.sort()

# In:  {"foo":["bbb","ccc","aaa"]}
# Out: {"sorted":["aaa","bbb","ccc"]}
```

It's also possible to specify a mapping argument, which is provided an object context with fields `left` and `right`, the mapping must return a boolean indicating whether the `left` value is less than `right`. This allows you to sort arrays containing non-string or non-number values.

```coffee
root.sorted = this.foo.sort(item -> item.left.v < item.right.v)

# In:  {"foo":[{"id":"foo","v":"bbb"},{"id":"bar","v":"ccc"},{"id":"baz","v":"aaa"}]}
# Out: {"sorted":[{"id":"baz","v":"aaa"},{"id":"foo","v":"bbb"},{"id":"bar","v":"ccc"}]}
```

### sort_by

Attempts to sort the elements of an array, in increasing order, by a value emitted by an argument query applied to each element. The type of all values must match in order for the ordering to succeed. Supports string and number values.

#### Parameters

**query** &lt;query expression&gt; A query to apply to each element that yields a value used for sorting.  

#### Examples


```coffee
root.sorted = this.foo.sort_by(ele -> ele.id)

# In:  {"foo":[{"id":"bbb","message":"bar"},{"id":"aaa","message":"foo"},{"id":"ccc","message":"baz"}]}
# Out: {"sorted":[{"id":"aaa","message":"foo"},{"id":"bbb","message":"bar"},{"id":"ccc","message":"baz"}]}
```

### squash

Squashes an array of objects into a single object, where key collisions result in the values being merged (following similar rules as the `.merge()` method)

#### Examples


```coffee
root.locations = this.locations.map_each(loc -> {loc.state: [loc.name]}).squash()

# In:  {"locations":[{"name":"Seattle","state":"WA"},{"name":"New York","state":"NY"},{"name":"Bellevue","state":"WA"},{"name":"Olympia","state":"WA"}]}
# Out: {"locations":{"NY":["New York"],"WA":["Seattle","Bellevue","Olympia"]}}
```

### sum

Sum the numerical values of an array.

#### Examples


```coffee
root.sum = this.foo.sum()

# In:  {"foo":[3,8,4]}
# Out: {"sum":15}
```

### unique

Attempts to remove duplicate values from an array. The array may contain a combination of different value types, but numbers and strings are checked separately (`"5"` is a different element to `5`).

#### Parameters

**emit** &lt;(optional) query expression&gt; An optional query that can be used in order to yield a value for each element to determine uniqueness.  

#### Examples


```coffee
root.uniques = this.foo.unique()

# In:  {"foo":["a","b","a","c"]}
# Out: {"uniques":["a","b","c"]}
```

### values

Returns the values of an object as an array. The order of the resulting array will be random.

#### Examples


```coffee
root.foo_vals = this.foo.values().sort()

# In:  {"foo":{"bar":1,"baz":2}}
# Out: {"foo_vals":[1,2]}
```

### with

Returns an object where all but one or more [field path]({{< ref "/product-stack/tyk-streaming/configuration/common-configuration/field-paths" >}}) arguments are removed. Each path specifies a specific field to be retained from the input object, allowing for nested fields.

If a key within a nested path does not exist then it is ignored.

#### Examples


```coffee
root = this.with("inner.a","inner.c","d")

# In:  {"inner":{"a":"first","b":"second","c":"third"},"d":"fourth","e":"fifth"}
# Out: {"d":"fourth","inner":{"a":"first","c":"third"}}
```

### without

Returns an object where one or more [field path]({{< ref "/product-stack/tyk-streaming/configuration/common-configuration/field-paths" >}}) arguments are removed. Each path specifies a specific field to be deleted from the input object, allowing for nested fields.

If a key within a nested path does not exist or is not an object then it is not removed.

#### Examples


```coffee
root = this.without("inner.a","inner.c","d")

# In:  {"inner":{"a":"first","b":"second","c":"third"},"d":"fourth","e":"fifth"}
# Out: {"e":"fifth","inner":{"b":"second"}}
```

### zip

Zip an array value with one or more argument arrays. Each array must match in length.

#### Examples


```coffee
root.foo = this.foo.zip(this.bar, this.baz)

# In:  {"foo":["a","b","c"],"bar":[1,2,3],"baz":[4,5,6]}
# Out: {"foo":[["a",1,4],["b",2,5],["c",3,6]]}
```

## Parsing

### bloblang

Executes an argument [Bloblang]({< ref "/product-stack/tyk-streaming/guides/bloblang/overview" >}) mapping on the target. This method can be used in order to execute dynamic mappings. Imports and functions that interact with the environment, such as `file` and `env`, or that access message information directly, such as `content` or `json`, are not enabled for dynamic [Bloblang]({< ref "/product-stack/tyk-streaming/guides/bloblang/overview" >}) mappings.

#### Parameters

**mapping** &lt;string&gt; The mapping to execute.  

#### Examples


```coffee
root.body = this.body.bloblang(this.mapping)

# In:  {"body":{"foo":"hello world"},"mapping":"root.foo = this.foo.uppercase()"}
# Out: {"body":{"foo":"HELLO WORLD"}}

# In:  {"body":{"foo":"hello world 2"},"mapping":"root.foo = this.foo.capitalize()"}
# Out: {"body":{"foo":"Hello World 2"}}
```

### format_json

Serializes a target value into a pretty-printed JSON byte array (with 4 space indentation by default).

#### Parameters

**indent** &lt;string, default `"    "`&gt; Indentation string. Each element in a JSON object or array will begin on a new, indented line followed by one or more copies of indent according to the indentation nesting.  
**no_indent** &lt;bool, default `false`&gt; Disable indentation.  

#### Examples


```coffee
root = this.doc.format_json()

# In:  {"doc":{"foo":"bar"}}
# Out: {
#          "foo": "bar"
#      }
```

Pass a string to the `indent` parameter in order to customise the indentation.

```coffee
root = this.format_json("  ")

# In:  {"doc":{"foo":"bar"}}
# Out: {
#        "doc": {
#          "foo": "bar"
#        }
#      }
```

Use the `.string()` method in order to coerce the result into a string.

```coffee
root.doc = this.doc.format_json().string()

# In:  {"doc":{"foo":"bar"}}
# Out: {"doc":"{\n    \"foo\": \"bar\"\n}"}
```

Set the `no_indent` parameter to true to disable indentation. The result is equivalent to calling `bytes()`.

```coffee
root = this.doc.format_json(no_indent: true)

# In:  {"doc":{"foo":"bar"}}
# Out: {"foo":"bar"}
```

### format_msgpack

Formats data as a [MessagePack](https://msgpack.org/) message in bytes format.

#### Examples


```coffee
root = this.format_msgpack().encode("hex")

# In:  {"foo":"bar"}
# Out: 81a3666f6fa3626172
```

```coffee
root.encoded = this.format_msgpack().encode("base64")

# In:  {"foo":"bar"}
# Out: {"encoded":"gaNmb2+jYmFy"}
```

### format_xml

Serializes a target value into an XML byte array.


#### Parameters

**indent** &lt;string, default `"    "`&gt; Indentation string. Each element in an XML object or array will begin on a new, indented line followed by one or more copies of indent according to the indentation nesting.  
**no_indent** &lt;bool, default `false`&gt; Disable indentation.  

#### Examples


Serializes a target value into a pretty-printed XML byte array (with 4 space indentation by default).

```coffee
root = this.format_xml()

# In:  {"foo":{"bar":{"baz":"foo bar baz"}}}
# Out: <foo>
#          <bar>
#              <baz>foo bar baz</baz>
#          </bar>
#      </foo>
```

Pass a string to the `indent` parameter in order to customise the indentation.

```coffee
root = this.format_xml("  ")

# In:  {"foo":{"bar":{"baz":"foo bar baz"}}}
# Out: <foo>
#        <bar>
#          <baz>foo bar baz</baz>
#        </bar>
#      </foo>
```

Use the `.string()` method in order to coerce the result into a string.

```coffee
root.doc = this.format_xml("").string()

# In:  {"foo":{"bar":{"baz":"foo bar baz"}}}
# Out: {"doc":"<foo>\n<bar>\n<baz>foo bar baz</baz>\n</bar>\n</foo>"}
```

Set the `no_indent` parameter to true to disable indentation.

```coffee
root = this.format_xml(no_indent: true)

# In:  {"foo":{"bar":{"baz":"foo bar baz"}}}
# Out: <foo><bar><baz>foo bar baz</baz></bar></foo>
```

### format_yaml

Serializes a target value into a YAML byte array.

#### Examples


```coffee
root = this.doc.format_yaml()

# In:  {"doc":{"foo":"bar"}}
# Out: foo: bar
```

Use the `.string()` method in order to coerce the result into a string.

```coffee
root.doc = this.doc.format_yaml().string()

# In:  {"doc":{"foo":"bar"}}
# Out: {"doc":"foo: bar\n"}
```

### parse_csv

Attempts to parse a string into an array of objects by following the CSV format described in RFC 4180.

#### Parameters

**parse_header_row** &lt;bool, default `true`&gt; Whether to reference the first row as a header row. If set to true the output structure for messages will be an object where field keys are determined by the header row. Otherwise, the output will be an array of row arrays.  
**delimiter** &lt;string, default `","`&gt; The delimiter to use for splitting values in each record. It must be a single character.  
**lazy_quotes** &lt;bool, default `false`&gt; If set to `true`, a quote may appear in an unquoted field and a non-doubled quote may appear in a quoted field.  

#### Examples


Parses CSV data with a header row

```coffee
root.orders = this.orders.parse_csv()

# In:  {"orders":"foo,bar\nfoo 1,bar 1\nfoo 2,bar 2"}
# Out: {"orders":[{"bar":"bar 1","foo":"foo 1"},{"bar":"bar 2","foo":"foo 2"}]}
```

Parses CSV data without a header row

```coffee
root.orders = this.orders.parse_csv(false)

# In:  {"orders":"foo 1,bar 1\nfoo 2,bar 2"}
# Out: {"orders":[["foo 1","bar 1"],["foo 2","bar 2"]]}
```

Parses CSV data delimited by dots

```coffee
root.orders = this.orders.parse_csv(delimiter:".")

# In:  {"orders":"foo.bar\nfoo 1.bar 1\nfoo 2.bar 2"}
# Out: {"orders":[{"bar":"bar 1","foo":"foo 1"},{"bar":"bar 2","foo":"foo 2"}]}
```

Parses CSV data containing a quote in an unquoted field

```coffee
root.orders = this.orders.parse_csv(lazy_quotes:true)

# In:  {"orders":"foo,bar\nfoo 1,bar 1\nfoo\" \"2,bar\" \"2"}
# Out: {"orders":[{"bar":"bar 1","foo":"foo 1"},{"bar":"bar\" \"2","foo":"foo\" \"2"}]}
```

### parse_form_url_encoded

Attempts to parse a url-encoded query string (from an x-www-form-urlencoded request body) and returns a structured result.

#### Examples


```coffee
root.values = this.body.parse_form_url_encoded()

# In:  {"body":"noise=meow&animal=cat&fur=orange&fur=fluffy"}
# Out: {"values":{"animal":"cat","fur":["orange","fluffy"],"noise":"meow"}}
```

### parse_json

Attempts to parse a string as a JSON document and returns the result.

#### Parameters

**use_number** &lt;(optional) bool&gt; An optional flag that when set makes parsing numbers as json.Number instead of the default float64.  

#### Examples


```coffee
root.doc = this.doc.parse_json()

# In:  {"doc":"{\"foo\":\"bar\"}"}
# Out: {"doc":{"foo":"bar"}}
```

```coffee
root.doc = this.doc.parse_json(use_number: true)

# In:  {"doc":"{\"foo\":\"11380878173205700000000000000000000000000000000\"}"}
# Out: {"doc":{"foo":"11380878173205700000000000000000000000000000000"}}
```

### parse_msgpack

Parses a [MessagePack](https://msgpack.org/) message into a structured document.

#### Examples


```coffee
root = content().decode("hex").parse_msgpack()

# In:  81a3666f6fa3626172
# Out: {"foo":"bar"}
```

```coffee
root = this.encoded.decode("base64").parse_msgpack()

# In:  {"encoded":"gaNmb2+jYmFy"}
# Out: {"foo":"bar"}
```

### parse_parquet

Decodes a [Parquet file](https://parquet.apache.org/docs/) into an array of objects, one for each row within the file.

#### Parameters

**byte_array_as_string** &lt;bool, default `false`&gt; Deprecated: This parameter is no longer used.  

#### Examples


```coffee
root = content().parse_parquet()
```

### parse_url

Attempts to parse a URL from a string value, returning a structured result that describes the various facets of the URL. The fields returned within the structured result roughly follow https://pkg.go.dev/net/url#URL, and may be expanded in future in order to present more information.

#### Examples


```coffee
root.foo_url = this.foo_url.parse_url()

# In:  {"foo_url":"https://tyk.io/docs/product-stack/tyk-streaming/overview/"}
# Out: {"foo_url":{"fragment":"","host":"tyk.io","opaque":"","path":"/docs/product-stack/tyk-streaming/overview/","raw_fragment":"","raw_path":"","raw_query":"","scheme":"https"}}
```

```coffee
root.username = this.url.parse_url().user.name | "unknown"

# In:  {"url":"amqp://foo:bar@127.0.0.1:5672/"}
# Out: {"username":"foo"}

# In:  {"url":"redis://localhost:6379"}
# Out: {"username":"unknown"}
```

### parse_xml

Attempts to parse a string as an XML document and returns a structured result, where elements appear as keys of an object according to the following rules:

- If an element contains attributes they are parsed by prefixing a hyphen, `-`, to the attribute label.
- If the element is a simple element and has attributes, the element value is given the key `#text`.
- XML comments, directives, and process instructions are ignored.
- When elements are repeated the resulting JSON value is an array.
- If cast is true, try to cast values to numbers and booleans instead of returning strings.


#### Parameters

**cast** &lt;(optional) bool, default `false`&gt; whether to try to cast values that are numbers and booleans to the right type.  

#### Examples


```coffee
root.doc = this.doc.parse_xml()

# In:  {"doc":"<root><title>This is a title</title><content>This is some content</content></root>"}
# Out: {"doc":{"root":{"content":"This is some content","title":"This is a title"}}}
```

```coffee
root.doc = this.doc.parse_xml(cast: false)

# In:  {"doc":"<root><title>This is a title</title><number id=99>123</number><bool>True</bool></root>"}
# Out: {"doc":{"root":{"bool":"True","number":{"#text":"123","-id":"99"},"title":"This is a title"}}}
```

```coffee
root.doc = this.doc.parse_xml(cast: true)

# In:  {"doc":"<root><title>This is a title</title><number id=99>123</number><bool>True</bool></root>"}
# Out: {"doc":{"root":{"bool":true,"number":{"#text":123,"-id":99},"title":"This is a title"}}}
```

### parse_yaml

Attempts to parse a string as a single YAML document and returns the result.

#### Examples


```coffee
root.doc = this.doc.parse_yaml()

# In:  {"doc":"foo: bar"}
# Out: {"doc":{"foo":"bar"}}
```

## Encoding and Encryption

### compress

Compresses a string or byte array value according to a specified algorithm.

#### Parameters

**algorithm** &lt;string&gt; One of `flate`, `gzip`, `pgzip`, `lz4`, `snappy`, `zlib`, `zstd`.  
**level** &lt;integer, default `-1`&gt; The level of compression to use. May not be applicable to all algorithms.  

#### Examples


```coffee
let long_content = range(0, 1000).map_each(content()).join(" ")
root.a_len = $long_content.length()
root.b_len = $long_content.compress("gzip").length()


# In:  hello world this is some content
# Out: {"a_len":32999,"b_len":161}
```

```coffee
root.compressed = content().compress("lz4").encode("base64")

# In:  hello world I love space
# Out: {"compressed":"BCJNGGRwuRgAAIBoZWxsbyB3b3JsZCBJIGxvdmUgc3BhY2UAAAAAGoETLg=="}
```

### decode

Decodes an encoded string target according to a chosen scheme and returns the result as a byte array. When mapping the result to a JSON field the value should be cast to a string using the method [string](#string, or encoded using the method [encode](#encode), otherwise it will be base64 encoded by default.

Available schemes are: `base64`, `base64url` [(RFC 4648 with padding characters)](https://rfc-editor.org/rfc/rfc4648.html), `base64rawurl` [(RFC 4648 without padding characters)](https://rfc-editor.org/rfc/rfc4648.html), `hex` and `ascii85`.

#### Parameters

**scheme** &lt;string&gt; The decoding scheme to use.  

#### Examples


```coffee
root.decoded = this.value.decode("hex").string()

# In:  {"value":"68656c6c6f20776f726c64"}
# Out: {"decoded":"hello world"}
```

```coffee
root = this.encoded.decode("ascii85")

# In:  {"encoded":"FD,B0+DGm>FDl80Ci\"A>F`)8BEckl6F`M&(+Cno&@/"}
# Out: this is totally unstructured data
```

### decompress

Decompresses a string or byte array value according to a specified algorithm. The result of decompression 

#### Parameters

**algorithm** &lt;string&gt; One of `gzip`, `pgzip`, `zlib`, `bzip2`, `flate`, `snappy`, `lz4`, `zstd`.  

#### Examples


```coffee
root = this.compressed.decode("base64").decompress("lz4")

# In:  {"compressed":"BCJNGGRwuRgAAIBoZWxsbyB3b3JsZCBJIGxvdmUgc3BhY2UAAAAAGoETLg=="}
# Out: hello world I love space
```

Use the `.string()` method in order to coerce the result into a string, this makes it possible to place the data within a JSON document without automatic base64 encoding.

```coffee
root.result = this.compressed.decode("base64").decompress("lz4").string()

# In:  {"compressed":"BCJNGGRwuRgAAIBoZWxsbyB3b3JsZCBJIGxvdmUgc3BhY2UAAAAAGoETLg=="}
# Out: {"result":"hello world I love space"}
```

### decrypt_aes

Decrypts an encrypted string or byte array target according to a chosen AES encryption method and returns the result as a byte array. The algorithms require a key and an initialization vector / nonce. Available schemes are: `ctr`, `ofb`, `cbc`.

#### Parameters

**scheme** &lt;string&gt; The scheme to use for decryption, one of `ctr`, `ofb`, `cbc`.  
**key** &lt;string&gt; A key to decrypt with.  
**iv** &lt;string&gt; An initialization vector / nonce.  

#### Examples


```coffee
let key = "2b7e151628aed2a6abf7158809cf4f3c".decode("hex")
let vector = "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff".decode("hex")
root.decrypted = this.value.decode("hex").decrypt_aes("ctr", $key, $vector).string()

# In:  {"value":"84e9b31ff7400bdf80be7254"}
# Out: {"decrypted":"hello world!"}
```

### encode

Encodes a string or byte array target according to a chosen scheme and returns a string result. Available schemes are: `base64`, `base64url` [(RFC 4648 with padding characters)](https://rfc-editor.org/rfc/rfc4648.html), `base64rawurl` [(RFC 4648 without padding characters)](https://rfc-editor.org/rfc/rfc4648.html), `hex`, `ascii85`.

#### Parameters

**scheme** &lt;string&gt; The encoding scheme to use.  

#### Examples


```coffee
root.encoded = this.value.encode("hex")

# In:  {"value":"hello world"}
# Out: {"encoded":"68656c6c6f20776f726c64"}
```

```coffee
root.encoded = content().encode("ascii85")

# In:  this is totally unstructured data
# Out: {"encoded":"FD,B0+DGm>FDl80Ci\"A>F`)8BEckl6F`M&(+Cno&@/"}
```

### encrypt_aes

Encrypts a string or byte array target according to a chosen AES encryption method and returns a string result. The algorithms require a key and an initialization vector / nonce. Available schemes are: `ctr`, `ofb`, `cbc`.

#### Parameters

**scheme** &lt;string&gt; The scheme to use for encryption, one of `ctr`, `ofb`, `cbc`.  
**key** &lt;string&gt; A key to encrypt with.  
**iv** &lt;string&gt; An initialization vector / nonce.  

#### Examples


```coffee
let key = "2b7e151628aed2a6abf7158809cf4f3c".decode("hex")
let vector = "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff".decode("hex")
root.encrypted = this.value.encrypt_aes("ctr", $key, $vector).encode("hex")

# In:  {"value":"hello world!"}
# Out: {"encrypted":"84e9b31ff7400bdf80be7254"}
```

### hash

Hashes a string or byte array according to a chosen algorithm and returns the result as a byte array. When mapping the result to a JSON field the value should be cast to a string using the method [string][methods.string], or encoded using the method [encode][methods.encode], otherwise it will be base64 encoded by default.

Available algorithms are: `hmac_sha1`, `hmac_sha256`, `hmac_sha512`, `md5`, `sha1`, `sha256`, `sha512`, `xxhash64`, `crc32`.

The following algorithms require a key, which is specified as a second argument: `hmac_sha1`, `hmac_sha256`, `hmac_sha512`.

#### Parameters

**algorithm** &lt;string&gt; The hasing algorithm to use.  
**key** &lt;(optional) string&gt; An optional key to use.  
**polynomial** &lt;string, default `"IEEE"`&gt; An optional polynomial key to use when selecting the `crc32` algorithm, otherwise ignored. Options are `IEEE` (default), `Castagnoli` and `Koopman`  

#### Examples


```coffee
root.h1 = this.value.hash("sha1").encode("hex")
root.h2 = this.value.hash("hmac_sha1","static-key").encode("hex")

# In:  {"value":"hello world"}
# Out: {"h1":"2aae6c35c94fcfb415dbe95f408b9ce91ee846ed","h2":"d87e5f068fa08fe90bb95bc7c8344cb809179d76"}
```

The crc32 algorithm supports options for the polynomial.

```coffee
root.h1 = this.value.hash(algorithm: "crc32", polynomial: "Castagnoli").encode("hex")
root.h2 = this.value.hash(algorithm: "crc32", polynomial: "Koopman").encode("hex")

# In:  {"value":"hello world"}
# Out: {"h1":"c99465aa","h2":"df373d3c"}
```

## JSON Web Tokens

### parse_jwt_es256

Parses a claims object from a JWT string encoded with ES256. This method does not validate JWT claims.

#### Parameters

**signing_secret** &lt;string&gt; The ES256 secret that was used for signing the token.  

#### Examples


```coffee
root.claims = this.signed.parse_jwt_es256("""-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEGtLqIBePHmIhQcf0JLgc+F/4W/oI
dp0Gta53G35VerNDgUUXmp78J2kfh4qLdh0XtmOMI587tCaqjvDAXfs//w==
-----END PUBLIC KEY-----""")

# In:  {"signed":"eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjIsIm1vb2QiOiJEaXNkYWluZnVsIiwic3ViIjoiMTIzNDU2Nzg5MCJ9.GIRajP9JJbpTlqSCdNEz4qpQkRvzX4Q51YnTwVyxLDM9tKjR_a8ggHWn9CWj7KG0x8J56OWtmUxn112SRTZVhQ"}
# Out: {"claims":{"iat":1516239022,"mood":"Disdainful","sub":"1234567890"}}
```

### parse_jwt_es384

Parses a claims object from a JWT string encoded with ES384. This method does not validate JWT claims.

#### Parameters

**signing_secret** &lt;string&gt; The ES384 secret that was used for signing the token.  

#### Examples


```coffee
root.claims = this.signed.parse_jwt_es384("""-----BEGIN PUBLIC KEY-----
MHYwEAYHKoZIzj0CAQYFK4EEACIDYgAERoz74/B6SwmLhs8X7CWhnrWyRrB13AuU
8OYeqy0qHRu9JWNw8NIavqpTmu6XPT4xcFanYjq8FbeuM11eq06C52mNmS4LLwzA
2imlFEgn85bvJoC3bnkuq4mQjwt9VxdH
-----END PUBLIC KEY-----""")

# In:  {"signed":"eyJhbGciOiJFUzM4NCIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjIsIm1vb2QiOiJEaXNkYWluZnVsIiwic3ViIjoiMTIzNDU2Nzg5MCJ9.H2HBSlrvQBaov2tdreGonbBexxtQB-xzaPL4-tNQZ6TVh7VH8VBcSwcWHYa1lBAHmdsKOFcB2Wk0SB7QWeGT3ptSgr-_EhDMaZ8bA5spgdpq5DsKfaKHrd7DbbQlmxNq"}
# Out: {"claims":{"iat":1516239022,"mood":"Disdainful","sub":"1234567890"}}
```

### parse_jwt_es512

Parses a claims object from a JWT string encoded with ES512. This method does not validate JWT claims.

#### Parameters

**signing_secret** &lt;string&gt; The ES512 secret that was used for signing the token.  

#### Examples


```coffee
root.claims = this.signed.parse_jwt_es512("""-----BEGIN PUBLIC KEY-----
MIGbMBAGByqGSM49AgEGBSuBBAAjA4GGAAQAkHLdts9P56fFkyhpYQ31M/Stwt3w
vpaxhlfudxnXgTO1IP4RQRgryRxZ19EUzhvWDcG3GQIckoNMY5PelsnCGnIBT2Xh
9NQkjWF5K6xS4upFsbGSAwQ+GIyyk5IPJ2LHgOyMSCVh5gRZXV3CZLzXujx/umC9
UeYyTt05zRRWuD+p5bY=
-----END PUBLIC KEY-----""")

# In:  {"signed":"eyJhbGciOiJFUzUxMiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjIsIm1vb2QiOiJEaXNkYWluZnVsIiwic3ViIjoiMTIzNDU2Nzg5MCJ9.ACrpLuU7TKpAnncDCpN9m85nkL55MJ45NFOBl6-nEXmNT1eIxWjiP4pwWVbFH9et_BgN14119jbL_KqEJInPYc9nAXC6dDLq0aBU-dalvNl4-O5YWpP43-Y-TBGAsWnbMTrchILJ4-AEiICe73Ck5yWPleKg9c3LtkEFWfGs7BoPRguZ"}
# Out: {"claims":{"iat":1516239022,"mood":"Disdainful","sub":"1234567890"}}
```

### parse_jwt_hs256

Parses a claims object from a JWT string encoded with HS256. This method does not validate JWT claims.

#### Parameters

**signing_secret** &lt;string&gt; The HS256 secret that was used for signing the token.  

#### Examples


```coffee
root.claims = this.signed.parse_jwt_hs256("""dont-tell-anyone""")

# In:  {"signed":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjIsIm1vb2QiOiJEaXNkYWluZnVsIiwic3ViIjoiMTIzNDU2Nzg5MCJ9.YwXOM8v3gHVWcQRRRQc_zDlhmLnM62fwhFYGpiA0J1A"}
# Out: {"claims":{"iat":1516239022,"mood":"Disdainful","sub":"1234567890"}}
```

### parse_jwt_hs384

Parses a claims object from a JWT string encoded with HS384. This method does not validate JWT claims.

#### Parameters

**signing_secret** &lt;string&gt; The HS384 secret that was used for signing the token.  

#### Examples


```coffee
root.claims = this.signed.parse_jwt_hs384("""dont-tell-anyone""")

# In:  {"signed":"eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjIsIm1vb2QiOiJEaXNkYWluZnVsIiwic3ViIjoiMTIzNDU2Nzg5MCJ9.2Y8rf_ijwN4t8hOGGViON_GrirLkCQVbCOuax6EoZ3nluX0tCGezcJxbctlIfsQ2"}
# Out: {"claims":{"iat":1516239022,"mood":"Disdainful","sub":"1234567890"}}
```

### parse_jwt_hs512

Parses a claims object from a JWT string encoded with HS512. This method does not validate JWT claims.

#### Parameters

**signing_secret** &lt;string&gt; The HS512 secret that was used for signing the token.  

#### Examples


```coffee
root.claims = this.signed.parse_jwt_hs512("""dont-tell-anyone""")

# In:  {"signed":"eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjIsIm1vb2QiOiJEaXNkYWluZnVsIiwic3ViIjoiMTIzNDU2Nzg5MCJ9.utRb0urG6LGGyranZJVo5Dk0Fns1QNcSUYPN0TObQ-YzsGGB8jrxHwM5NAJccjJZzKectEUqmmKCaETZvuX4Fg"}
# Out: {"claims":{"iat":1516239022,"mood":"Disdainful","sub":"1234567890"}}
```

### parse_jwt_rs256

Parses a claims object from a JWT string encoded with RS256. This method does not validate JWT claims.

Introduced in version v4.20.0.


#### Parameters

**signing_secret** &lt;string&gt; The RS256 secret that was used for signing the token.  

#### Examples


```coffee
root.claims = this.signed.parse_jwt_rs256("""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAs/ibN8r68pLMR6gRzg4S
8v8l6Q7yi8qURjkEbcNeM1rkokC7xh0I4JVTwxYSVv/JIW8qJdyspl5NIfuAVi32
WfKvSAs+NIs+DMsNPYw3yuQals4AX8hith1YDvYpr8SD44jxhz/DR9lYKZFGhXGB
+7NqQ7vpTWp3BceLYocazWJgusZt7CgecIq57ycM5hjM93BvlrUJ8nQ1a46wfL/8
Cy4P0et70hzZrsjjN41KFhKY0iUwlyU41yEiDHvHDDsTMBxAZosWjSREGfJL6Mfp
XOInTHs/Gg6DZMkbxjQu6L06EdJ+Q/NwglJdAXM7Zo9rNELqRig6DdvG5JesdMsO
+QIDAQAB
-----END PUBLIC KEY-----""")

# In:  {"signed":"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjIsIm1vb2QiOiJEaXNkYWluZnVsIiwic3ViIjoiMTIzNDU2Nzg5MCJ9.b0lH3jEupZZ4zoaly4Y_GCvu94HH6UKdKY96zfGNsIkPZpQLHIkZ7jMWlLlNOAd8qXlsBGP_i8H2qCKI4zlWJBGyPZgxXDzNRPVrTDfFpn4t4nBcA1WK2-ntXP3ehQxsaHcQU8Z_nsogId7Pme5iJRnoHWEnWtbwz5DLSXL3ZZNnRdrHM9MdI7QSDz9mojKDCaMpGN9sG7Xl-tGdBp1XzXuUOzG8S03mtZ1IgVR1uiBL2N6oohHIAunk8DIAmNWI-zgycTgzUGU7mvPkKH43qO8Ua1-13tCUBKKa8VxcotZ67Mxm1QAvBGoDnTKwWMwghLzs6d6WViXQg6eWlJcpBA"}
# Out: {"claims":{"iat":1516239022,"mood":"Disdainful","sub":"1234567890"}}
```

### parse_jwt_rs384

Parses a claims object from a JWT string encoded with RS384. This method does not validate JWT claims.

#### Parameters

**signing_secret** &lt;string&gt; The RS384 secret that was used for signing the token.  

#### Examples


```coffee
root.claims = this.signed.parse_jwt_rs384("""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAs/ibN8r68pLMR6gRzg4S
8v8l6Q7yi8qURjkEbcNeM1rkokC7xh0I4JVTwxYSVv/JIW8qJdyspl5NIfuAVi32
WfKvSAs+NIs+DMsNPYw3yuQals4AX8hith1YDvYpr8SD44jxhz/DR9lYKZFGhXGB
+7NqQ7vpTWp3BceLYocazWJgusZt7CgecIq57ycM5hjM93BvlrUJ8nQ1a46wfL/8
Cy4P0et70hzZrsjjN41KFhKY0iUwlyU41yEiDHvHDDsTMBxAZosWjSREGfJL6Mfp
XOInTHs/Gg6DZMkbxjQu6L06EdJ+Q/NwglJdAXM7Zo9rNELqRig6DdvG5JesdMsO
+QIDAQAB
-----END PUBLIC KEY-----""")

# In:  {"signed":"eyJhbGciOiJSUzM4NCIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjIsIm1vb2QiOiJEaXNkYWluZnVsIiwic3ViIjoiMTIzNDU2Nzg5MCJ9.orcXYBcjVE5DU7mvq4KKWFfNdXR4nEY_xupzWoETRpYmQZIozlZnM_nHxEk2dySvpXlAzVm7kgOPK2RFtGlOVaNRIa3x-pMMr-bhZTno4L8Hl4sYxOks3bWtjK7wql4uqUbqThSJB12psAXw2-S-I_FMngOPGIn4jDT9b802ottJSvTpXcy0-eKTjrV2PSkRRu-EYJh0CJZW55MNhqlt6kCGhAXfbhNazN3ASX-dmpd_JixyBKphrngr_zRA-FCn_Xf3QQDA-5INopb4Yp5QiJ7UxVqQEKI80X_JvJqz9WE1qiAw8pq5-xTen1t7zTP-HT1NbbD3kltcNa3G8acmNg"}
# Out: {"claims":{"iat":1516239022,"mood":"Disdainful","sub":"1234567890"}}
```

### parse_jwt_rs512

Parses a claims object from a JWT string encoded with RS512. This method does not validate JWT claims.

#### Parameters

**signing_secret** &lt;string&gt; The RS512 secret that was used for signing the token.  

#### Examples


```coffee
root.claims = this.signed.parse_jwt_rs512("""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAs/ibN8r68pLMR6gRzg4S
8v8l6Q7yi8qURjkEbcNeM1rkokC7xh0I4JVTwxYSVv/JIW8qJdyspl5NIfuAVi32
WfKvSAs+NIs+DMsNPYw3yuQals4AX8hith1YDvYpr8SD44jxhz/DR9lYKZFGhXGB
+7NqQ7vpTWp3BceLYocazWJgusZt7CgecIq57ycM5hjM93BvlrUJ8nQ1a46wfL/8
Cy4P0et70hzZrsjjN41KFhKY0iUwlyU41yEiDHvHDDsTMBxAZosWjSREGfJL6Mfp
XOInTHs/Gg6DZMkbxjQu6L06EdJ+Q/NwglJdAXM7Zo9rNELqRig6DdvG5JesdMsO
+QIDAQAB
-----END PUBLIC KEY-----""")

# In:  {"signed":"eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjIsIm1vb2QiOiJEaXNkYWluZnVsIiwic3ViIjoiMTIzNDU2Nzg5MCJ9.rsMp_X5HMrUqKnZJIxo27aAoscovRA6SSQYR9rq7pifIj0YHXxMyNyOBDGnvVALHKTi25VUGHpfNUW0VVMmae0A4t_ObNU6hVZHguWvetKZZq4FZpW1lgWHCMqgPGwT5_uOqwYCH6r8tJuZT3pqXeL0CY4putb1AN2w6CVp620nh3l8d3XWb4jaifycd_4CEVCqHuWDmohfug4VhmoVKlIXZkYoAQowgHlozATDssBSWdYtv107Wd2AzEoiXPu6e3pflsuXULlyqQnS4ELEKPYThFLafh1NqvZDPddqozcPZ-iODBW-xf3A4DYDdivnMYLrh73AZOGHexxu8ay6nDA"}
# Out: {"claims":{"iat":1516239022,"mood":"Disdainful","sub":"1234567890"}}
```

### sign_jwt_es256

Hash and sign an object representing JSON Web Token (JWT) claims using ES256.

#### Parameters

**signing_secret** &lt;string&gt; The secret to use for signing the token.  

#### Examples

```coffee
root.signed = this.claims.sign_jwt_es256("""-----BEGIN EC PRIVATE KEY-----
... signature data ...
-----END EC PRIVATE KEY-----""")

# In:  {"claims":{"sub":"user123"}}
# Out: {"signed":"eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjIsIm1vb2QiOiJEaXNkYWluZnVsIiwic3ViIjoiMTIzNDU2Nzg5MCJ9.-8LrOdkEiv_44ADWW08lpbq41ZmHCel58NMORPq1q4Dyw0zFhqDVLrRoSvCvuyyvgXAFb9IHfR-9MlJ_2ShA9A"}
```

### sign_jwt_es384

Hash and sign an object representing JSON Web Token (JWT) claims using ES384.

#### Parameters

**signing_secret** &lt;string&gt; The secret to use for signing the token.  

#### Examples

```coffee
root.signed = this.claims.sign_jwt_es384("""-----BEGIN EC PRIVATE KEY-----
... signature data ...
-----END EC PRIVATE KEY-----""")

# In:  {"claims":{"sub":"user123"}}
# Out: {"signed":"eyJhbGciOiJFUzM4NCIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIn0.8FmTKH08dl7dyxrNu0rmvhegiIBCy-O9cddGco2e9lpZtgv5mS5qHgPkgBC5eRw1d7SRJsHwHZeehzdqT5Ba7aZJIhz9ds0sn37YQ60L7jT0j2gxCzccrt4kECHnUnLw"}
```

### sign_jwt_es512

Hash and sign an object representing JSON Web Token (JWT) claims using ES512.

#### Parameters

**signing_secret** &lt;string&gt; The secret to use for signing the token.  

#### Examples


```coffee
root.signed = this.claims.sign_jwt_es512("""-----BEGIN EC PRIVATE KEY-----
... signature data ...
-----END EC PRIVATE KEY-----""")

# In:  {"claims":{"sub":"user123"}}
# Out: {"signed":"eyJhbGciOiJFUzUxMiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIn0.AQbEWymoRZxDJEJtKSFFG2k2VbDCTYSuBwAZyMqexCspr3If8aERTVGif8HXG3S7TzMBCCzxkcKr3eIU441l3DlpAMNfQbkcOlBqMvNBn-CX481WyKf3K5rFHQ-6wRonz05aIsWAxCDvAozI_9J0OWllxdQ2MBAuTPbPJ38OqXsYkCQs"}
```

### sign_jwt_hs256

Hash and sign an object representing JSON Web Token (JWT) claims using HS256.


#### Parameters

**signing_secret** &lt;string&gt; The secret to use for signing the token.  

#### Examples


```coffee
root.signed = this.claims.sign_jwt_hs256("""dont-tell-anyone""")

# In:  {"claims":{"sub":"user123"}}
# Out: {"signed":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIn0.hUl-nngPMY_3h9vveWJUPsCcO5PeL6k9hWLnMYeFbFQ"}
```

### sign_jwt_hs384

Hash and sign an object representing JSON Web Token (JWT) claims using HS384.

#### Parameters

**signing_secret** &lt;string&gt; The secret to use for signing the token.  

#### Examples


```coffee
root.signed = this.claims.sign_jwt_hs384("""dont-tell-anyone""")

# In:  {"claims":{"sub":"user123"}}
# Out: {"signed":"eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIn0.zGYLr83aToon1efUNq-hw7XgT20lPvZb8sYei8x6S6mpHwb433SJdXJXx0Oio8AZ"}
```

### sign_jwt_hs512

Hash and sign an object representing JSON Web Token (JWT) claims using HS512.

#### Parameters

**signing_secret** &lt;string&gt; The secret to use for signing the token.  

#### Examples


```coffee
root.signed = this.claims.sign_jwt_hs512("""dont-tell-anyone""")

# In:  {"claims":{"sub":"user123"}}
# Out: {"signed":"eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIn0.zBNR9o_6EDwXXKkpKLNJhG26j8Dc-mV-YahBwmEdCrmiWt5les8I9rgmNlWIowpq6Yxs4kLNAdFhqoRz3NXT3w"}
```

### sign_jwt_rs256

Hash and sign an object representing JSON Web Token (JWT) claims using RS256.

#### Parameters

**signing_secret** &lt;string&gt; The secret to use for signing the token.  

#### Examples


```coffee
root.signed = this.claims.sign_jwt_rs256("""-----BEGIN RSA PRIVATE KEY-----
... signature data ...
-----END RSA PRIVATE KEY-----""")

# In:  {"claims":{"sub":"user123"}}
# Out: {"signed":"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjIsIm1vb2QiOiJEaXNkYWluZnVsIiwic3ViIjoiMTIzNDU2Nzg5MCJ9.b0lH3jEupZZ4zoaly4Y_GCvu94HH6UKdKY96zfGNsIkPZpQLHIkZ7jMWlLlNOAd8qXlsBGP_i8H2qCKI4zlWJBGyPZgxXDzNRPVrTDfFpn4t4nBcA1WK2-ntXP3ehQxsaHcQU8Z_nsogId7Pme5iJRnoHWEnWtbwz5DLSXL3ZZNnRdrHM9MdI7QSDz9mojKDCaMpGN9sG7Xl-tGdBp1XzXuUOzG8S03mtZ1IgVR1uiBL2N6oohHIAunk8DIAmNWI-zgycTgzUGU7mvPkKH43qO8Ua1-13tCUBKKa8VxcotZ67Mxm1QAvBGoDnTKwWMwghLzs6d6WViXQg6eWlJcpBA"}
```

### sign_jwt_rs384

Hash and sign an object representing JSON Web Token (JWT) claims using RS384.

#### Parameters

**signing_secret** &lt;string&gt; The secret to use for signing the token.  

#### Examples


```coffee
root.signed = this.claims.sign_jwt_rs384("""-----BEGIN RSA PRIVATE KEY-----
... signature data ...
-----END RSA PRIVATE KEY-----""")

# In:  {"claims":{"sub":"user123"}}
# Out: {"signed":"eyJhbGciOiJSUzM4NCIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjIsIm1vb2QiOiJEaXNkYWluZnVsIiwic3ViIjoiMTIzNDU2Nzg5MCJ9.orcXYBcjVE5DU7mvq4KKWFfNdXR4nEY_xupzWoETRpYmQZIozlZnM_nHxEk2dySvpXlAzVm7kgOPK2RFtGlOVaNRIa3x-pMMr-bhZTno4L8Hl4sYxOks3bWtjK7wql4uqUbqThSJB12psAXw2-S-I_FMngOPGIn4jDT9b802ottJSvTpXcy0-eKTjrV2PSkRRu-EYJh0CJZW55MNhqlt6kCGhAXfbhNazN3ASX-dmpd_JixyBKphrngr_zRA-FCn_Xf3QQDA-5INopb4Yp5QiJ7UxVqQEKI80X_JvJqz9WE1qiAw8pq5-xTen1t7zTP-HT1NbbD3kltcNa3G8acmNg"}
```

### sign_jwt_rs512

Hash and sign an object representing JSON Web Token (JWT) claims using RS512.

#### Parameters

**signing_secret** &lt;string&gt; The secret to use for signing the token.  

#### Examples


```coffee
root.signed = this.claims.sign_jwt_rs512("""-----BEGIN RSA PRIVATE KEY-----
... signature data ...
-----END RSA PRIVATE KEY-----""")

# In:  {"claims":{"sub":"user123"}}
# Out: {"signed":"eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjIsIm1vb2QiOiJEaXNkYWluZnVsIiwic3ViIjoiMTIzNDU2Nzg5MCJ9.rsMp_X5HMrUqKnZJIxo27aAoscovRA6SSQYR9rq7pifIj0YHXxMyNyOBDGnvVALHKTi25VUGHpfNUW0VVMmae0A4t_ObNU6hVZHguWvetKZZq4FZpW1lgWHCMqgPGwT5_uOqwYCH6r8tJuZT3pqXeL0CY4putb1AN2w6CVp620nh3l8d3XWb4jaifycd_4CEVCqHuWDmohfug4VhmoVKlIXZkYoAQowgHlozATDssBSWdYtv107Wd2AzEoiXPu6e3pflsuXULlyqQnS4ELEKPYThFLafh1NqvZDPddqozcPZ-iODBW-xf3A4DYDdivnMYLrh73AZOGHexxu8ay6nDA"}
```

## GeoIP

### geoip_anonymous_ip

Looks up an IP address against a [MaxMind database file](https://www.maxmind.com/en/home) and, if found, returns an object describing the anonymous IP associated with it.

#### Parameters

**path** &lt;string&gt; A path to an mmdb (maxmind) file.  

### geoip_asn

Looks up an IP address against a [MaxMind database file](https://www.maxmind.com/en/home) and, if found, returns an object describing the ASN associated with it.

#### Parameters

**path** &lt;string&gt; A path to an mmdb (maxmind) file.  

### geoip_city

Looks up an IP address against a [MaxMind database file](https://www.maxmind.com/en/home) and, if found, returns an object describing the city associated with it.

#### Parameters

**path** &lt;string&gt; A path to an mmdb (maxmind) file.  

### geoip_connection_type

Looks up an IP address against a [MaxMind database file](https://www.maxmind.com/en/home) and, if found, returns an object describing the connection type associated with it.

#### Parameters

**path** &lt;string&gt; A path to an mmdb (maxmind) file.  

### geoip_country

Looks up an IP address against a [MaxMind database file](https://www.maxmind.com/en/home) and, if found, returns an object describing the country associated with it.

#### Parameters

**path** &lt;string&gt; A path to an mmdb (maxmind) file.  

### geoip_domain

Looks up an IP address against a [MaxMind database file](https://www.maxmind.com/en/home) and, if found, returns an object describing the domain associated with it.

#### Parameters

**path** &lt;string&gt; A path to an mmdb (maxmind) file.  

### geoip_enterprise

Looks up an IP address against a [MaxMind database file](https://www.maxmind.com/en/home) and, if found, returns an object describing the enterprise associated with it.

#### Parameters

**path** &lt;string&gt; A path to an mmdb (maxmind) file.  

### geoip_isp

Looks up an IP address against a [MaxMind database file](https://www.maxmind.com/en/home) and, if found, returns an object describing the ISP associated with it.

#### Parameters

**path** &lt;string&gt; A path to an mmdb (maxmind) file.  

## Deprecated

### format_timestamp

Attempts to format a timestamp value as a string according to a specified format, or RFC 3339 by default. Timestamp values can either be a numerical unix time in seconds (with up to nanosecond precision via decimals), or a string in RFC 3339 format.

The output format is defined by showing how the reference time, defined to be Mon Jan 2 15:04:05 -0700 MST 2006, would be displayed if it were the value. For an alternative way to specify formats check out the [ts_strftime](#ts_strftime) method.

#### Parameters

**format** &lt;string, default `"2006-01-02T15:04:05.999999999Z07:00"`&gt; The output format to use.  
**tz** &lt;(optional) string&gt; An optional timezone to use, otherwise the timezone of the input string is used, or in the case of unix timestamps the local timezone is used.  

### format_timestamp_strftime

Attempts to format a timestamp value as a string according to a specified strftime-compatible format. Timestamp values can either be a numerical unix time in seconds (with up to nanosecond precision via decimals), or a string in RFC 3339 format.

#### Parameters

**format** &lt;string&gt; The output format to use.  
**tz** &lt;(optional) string&gt; An optional timezone to use, otherwise the timezone of the input string is used.  

### format_timestamp_unix

Attempts to format a timestamp value as a unix timestamp. Timestamp values can either be a numerical unix time in seconds (with up to nanosecond precision via decimals), or a string in RFC 3339 format. The [ts_parse](#ts_parse) method can be used in order to parse different timestamp formats.

### format_timestamp_unix_micro

Attempts to format a timestamp value as a unix timestamp with microsecond precision. Timestamp values can either be a numerical unix time in seconds (with up to nanosecond precision via decimals), or a string in RFC 3339 format. The [ts_parse](#ts_parse) method can be used in order to parse different timestamp formats.

### format_timestamp_unix_milli

Attempts to format a timestamp value as a unix timestamp with millisecond precision. Timestamp values can either be a numerical unix time in seconds (with up to nanosecond precision via decimals), or a string in RFC 3339 format. The [ts_parse](#ts_parse) method can be used in order to parse different timestamp formats.

### format_timestamp_unix_nano

Attempts to format a timestamp value as a unix timestamp with nanosecond precision. Timestamp values can either be a numerical unix time in seconds (with up to nanosecond precision via decimals), or a string in RFC 3339 format. The [ts_parse](#ts_parse) method can be used in order to parse different timestamp formats.

### parse_timestamp

Attempts to parse a string as a timestamp following a specified format and outputs a timestamp, which can then be fed into methods such as [ts_format](#ts_format).

The input format is defined by showing how the reference time, defined to be Mon Jan 2 15:04:05 -0700 MST 2006, would be displayed if it were the value. For an alternative way to specify formats check out the [ts_strptime](#ts_strptime) method.

#### Parameters

**format** &lt;string&gt; The format of the target string.  

### parse_timestamp_strptime

Attempts to parse a string as a timestamp following a specified strptime-compatible format and outputs a timestamp, which can then be fed into [ts_format](#ts_format).

#### Parameters

**format** &lt;string&gt; The format of the target string.  