---
title: Using the Request Validation middleware with Tyk OAS APIs
date: 2024-02-02
description: "Using the Request Validation middleware with Tyk OAS APIs"
tags: ["request validation", "validate request", "middleware", "per-endpoint", "Tyk OAS", "Tyk OAS API"]
---

The [request validation]({{< ref "product-stack/tyk-gateway/middleware/validate-request-middleware" >}}) middleware provides a way to validate the presence, correctness, and conformity of HTTP requests to make sure they meet the expected format required by the upstream API endpoints.

The middleware is configured in the [Tyk OAS API Definition]({{< ref "tyk-apis/tyk-gateway-api/oas/x-tyk-oas-doc#operation" >}}). You can do this via the Tyk Dashboard API or in the API Designer.

If you're using the legacy Tyk Classic APIs, then check out the [Tyk Classic]({{< ref "product-stack/tyk-gateway/middleware/validate-request-tyk-classic" >}}) page.

## Request schema in OpenAPI Specification
The OpenAPI Specification supports the definition of a [schema](https://learn.openapis.org/specification/content.html#the-schema-object) to describe and limit the content of any field in an API request or response.

Tyk's request validation middleware automatically parses the schema for the request in the OpenAPI description part of the Tyk OAS API Definition and use this to compare against the incoming request.

The clever part is that in this schema you can reference another schema defined elsewhere in the API Definition; this lets you write complex validations very efficiently since you don’t need to re-define the validation for a particular object every time you wish to refer to it. At this time Tyk only supports local references to schema within the same API Definition.

As explained in the OpenAPI Initiative [documentation](https://learn.openapis.org/specification/parameters.html), the structure of an API request is described by two components:
 - parameters (headers, query parameters, path parameters)
 - request body (payload)

### Request parameters
The `parameters` field in the OpenAPI description is an array of `parameter objects` that each describe one parameter shared by all operations on that path (where an operation is a combination of HTTP method + path or, as Tyk calls it, an endpoint). Each `parameter` has two mandatory fields:
 - `in`: the location of the parameter (`path`, `query`, `header`)
 - `name`: a unique identifier within that location (i.e. no duplicate header names for a given operation/endpoint)

There are also optional `description` and `required` fields.

For each parameter, a schema can be declared that defines the `type` of data that can be stored (e.g. `boolean`, `string`) and any `example` or `default` values.

### Request body
The `requestBody` field in the OpenAPI description is a [Request Body Object](https://swagger.io/docs/specification/describing-request-body/). This has two optional fields (`description` and `required`) plus the `content` section which allows you to define schema for the expected payload. Different schemas can be declared for different media types that are identified by content-type (e.g. `application/json`, `application/xml`, `text/plain`).

## Automatically configure the middleware from the OpenAPI Document
When [importing]({{< ref "getting-started/using-oas-definitions/import-an-oas-api#tutorial-5-create-an-api-that-validates-the-request-payload" >}}) an OpenAPI Document to create a Tyk OAS API, you can automatically enable the request validation middleware for all endpoints in the Document that have defined schemas. If using the Tyk Dashboard API or Tyk Gateway API you can do this by setting the `validateRequest=true` query parameter, if using the API Designer, select the option on the import screen.

## Configuring the middleware in the Tyk OAS API Definition
The design of the Tyk OAS API Definition takes advantage of the `operationID` defined in the OpenAPI Document that declares both the path and method for which the middleware should be added.

The request validation middleware (`validateRequest`) can be added to the `operations` section of the Tyk OAS Extension (`x-tyk-api-gateway`) in your Tyk OAS API Definition for the appropriate `operationId` (as configured in the `paths` section of your OpenAPI Document).

The `validateRequest` object has the following configuration:
 - `enabled`: enable the middleware for the endpoint
 - `errorResponseeCode`: [optional] the HTTP status code to be returned if validation fails (this defaults to `HTTP 422 Unprocessable Entity` if not set)

For example:
```.json {hl_lines=["69-72"],linenos=true, linenostart=1}
{
    "components": {},
    "info": {
        "title": "example-validate-request",
        "version": "1.0.0"
    },
    "openapi": "3.0.3",
    "paths": {
        "/anything": {
            "get": {
                "operationId": "anythingget",
                "parameters": [
                    {
                        "in": "header",
                        "name": "X-Security",
                        "required": true,
                        "schema": {
                            "type": "boolean"
                        }
                    }
                ],                
                "requestBody": {
                    "required": true,
                    "content": {
                        "application/json": {
                            "schema": {
                                "properties": {
                                    "firstname": {
                                        "description": "The person's first name",
                                        "type": "string"
                                    },
                                    "lastname": {
                                        "description": "The person's last name",
                                        "type": "string"
                                    }
                                },
                            "type": "object"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": ""
                    }
                }
            }
        }
    },
    "x-tyk-api-gateway": {
        "info": {
            "name": "example-validate-request",
            "state": {
                "active": true
            }
        },
        "upstream": {
            "url": "http://httpbin.org/"
        },
        "server": {
            "listenPath": {
                "value": "/example-validate-request/",
                "strip": true
            }
        },
        "middleware": {
            "operations": {
                "anythingget": {
                    "validateRequest": {
                        "enabled": true,
                        "errorResponseCode": 400
                    }
                }
            }
        }
    }
}
```

In this example the request validation middleware has been configured for HTTP `GET` requests to the `/anything` endpoint. The middleware will check for the existence of a header named `X-Security` and the request body will be validated against the declared schema. If there is no match, the request will be rejected and Tyk will return `HTTP 400` (as configured in `errorResponseCode`).

The configuration above is a complete and valid Tyk OAS API Definition that you can import into Tyk to try out the mock response middleware.

## Configuring the middleware in the API Designer
Adding Request Validation to your API endpoints is easy when using the API Designer in the Tyk Dashboard, simply follow the steps taken in these short videos:

 < placeholder for video >


