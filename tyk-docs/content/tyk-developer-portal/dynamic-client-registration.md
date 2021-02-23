---
date: 2017-03-24T17:10:33Z
title: Portal Concepts
menu:
  main:
    parent: "Tyk Developer Portal"
weight: 1
---

## OAuth 2.0 Dynamic Client Registration Protocol (DCR)
Available on version 3.2.0 onwards - currently not generally available but if you want beta access, get in touch! 

# What is it? 

DCR is a protocol of the Internet Engineering Task Force put in place to set standards in the dynamic registration of clients with authorisation servers. 
We will go into the specifics of how it works in the context of Tyk, but if you are interested in reading the full RFC, go to: http://www.rfc-editor.org/info/rfc7591

# Why should I use it? 

DCR is a way for you to integrate your developer portal with an external identity provider such as Keycloack, Gluu, Auth0, Okta etc... 
The user won't see a difference, but when they register a client on the portal, Tyk will proxy that request to your identity provider(IdP) and you will be able to manage their access crendentials either from the IdP or from Tyk. 

Some of our users leverage external Identity Providers because they provide a variety of features to support organisations in managing identity in one place across all their stack. 

This feature is optional and you can still have a great level of security only using tyk as your identity provider. 

# I have an identity provider, how can connect it? 

Tyk making the intermediation, we recommend that you also read the documentation of your identity provider as there will be some steps to follow on your IDP and the flow below assumes that you have completed the steps on your IdP.

Gluu: https://www.gluu.org/how-to-dynamically-register-openid-connect-client/
Okta: https://developer.okta.com/docs/reference/api/oauth-clients/
Auth0: https://auth0.com/docs/applications/dynamic-client-registration
Keycloack: https://www.keycloak.org/docs/latest/securing_apps/#openid-connect-dynamic-client-registration
Other options include Azure, Amazon, Ping... 


## Step 1: Create an API with JWT Authentification mode
If you're not sure how to do that, refer to : [https://tyk.io/docs/getting-started/tutorials/create-api/]
In the "public key" section, make sure you enter your JWKS url. This should come from your identity provider. 

## Step 2: Enable DCR
Go to Portal Settings, in the security tab you should have a "Dynamic Client Registration" section. 
Enable DCR. 

## Step 3: Fill the fields

This step is a little more tricky and the information there will depend on your identity provider. Let's go field by field and take the example of Gluu as we go through: 

1. Select a ``provider``

We have tested DCR with the 4 identity providers highlighted above (Keycloack, Gluu, Auth0 and Okta). Gluu and Keycloack have some slight specificities. Hence why we require to explicitely state if you are using one of the two. If you are using any other IdP, select "other". 

2. Select one or more ``grant type``

Grant types are arguments passed to different endpoints in the OAuth protocol. For example Password or token credentials. In the RFC 7 common grant types are mentioned which can be selected in the UI, but you can also add your own string.
Recommended
* ``Authorization code`` Defined in https://tools.ietf.org/html/rfc6749#section-1.3.1
* ``Client credentials`` Defined in https://tools.ietf.org/html/rfc6749#section-4.4
* ``Refresh token`` Defined in https://tools.ietf.org/html/rfc6749#section-1.5
* ``JWT Bearer token`` Defined in https://tools.ietf.org/html/rfc7523 Value is ``urn:ietf:params:oauth:grant-type:jwt-bearer``
* ``SAML 2.0 Bearer Assertion`` Defined in https://tools.ietf.org/html/rfc7522 Value is ``urn:ietf:params:oauth:grant-type:saml2-bearer``

Legacy
* ``Implicit``Implicit grant type defined https://tools.ietf.org/html/rfc6749#section-1.3.2
* ``Password`` Your IdP (resource owner) password credentials as a grant type https://tools.ietf.org/html/rfc6749#section-1.3.3


Your IdP may allow other values such as the device_code grant for application not using a browser or with constrained input. 

3. Select a ``token endpoint auth method``

Specify which authentication method should be used for the token endpoint. 
* "None" if the client is public and does not have a 'secret'
* "Client secret post" if the client uses the HTTP POST parameters
* "Client secret basic" if the cleint uses HTTP basic 

4. Select one or more ``Response type``

``code`` used for the Authorization Code grant OAuth 2.0 flow. 
``token`` is used for implicit grant. 

There are more options for complex use cases, though you only need to pick Code or Token.

5. Enter an ``Identity Provider host`` URL

This is the URL of your IDP. For example https://gluu.do.myproject

6. Enter a ``Client registration endpoint`` URL 

Usually an extension of the Identity provider host URL

7. Initial ``registration access token`` (optional)

The use of an initial access token is only required when the authorisation server limits the parties that can register a client. The value comes from IdP. 


🎉 All done! 


# It's not working! help!
Mati to add more on debugging / where and how to find logs. 

# A step-by-step guide using Gluu
Mati to use his google docs and create step by step guide. 
