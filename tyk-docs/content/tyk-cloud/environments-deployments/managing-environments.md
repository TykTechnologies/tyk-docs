---
title: "Managing Environments in Tyk Cloud"
tags: ["Environments", "Tyk Cloud", "Control Plane", "Cloud Data Plane"]
description: "Learn how to manage Environments in Tyk Cloud"
aliases:
  - /tyk-cloud/environments-&-deployments/managing-environments
  - /tyk-cloud/environments-deployments/managing-environments
  - /tyk-cloud/getting-started-tyk-cloud/setup-environment
  - /tyk-cloud/create-environment
---

## Introduction

Environments are used to group your [Control Plane]({{< ref "tyk-cloud#glossary" >}}) and [Cloud Data Planes]({{< ref "tyk-cloud#glossary" >}}) into logical groups. For example you may want to create environments that reflect different departments of your organization.

{{< note success >}}
**Note**

The number of Environments you can create is determined by your [plan]({{< ref "tyk-cloud/account-billing#select-a-payment-plan" >}})
{{< /note >}}

## Prerequisites

The following [user roles]({{< ref "tyk-cloud/teams-users#assign-user-roles" >}}) can perform Environment Admin tasks:

- Org Admin
- Team Admin

You should also have created a team to assign to any new environment.

## Adding a New Environment

1. From the Environments screen, click **Add Environment**
2. Select the team you want to assign to the Environment
3. Give your new Environment a name
4. Click **Create**

## Editing an Existing Environment

An Org Admin can perform the following:

- Rename an Environment
- Delete an Environment

1. Click the environment Name from your list

{{< img src="/img/admin/tyk-cloud-edit-env.png" alt="Edit Environment Name" >}}

2. Click Edit

{{< img src="/img/admin/tyk-cloud-env-screen.png" alt="Env Edit Screen" >}}

3. You can now rename the environment, or delete it from your organization

{{< img src="/img/admin/tyk-cloud-rename-delete.png" alt="Delete or Rename Env" >}}

{{< warning success >}}
**Warning**

Deleting an environment will also delete all the Control Planes and Cloud Data Planes associated with it
{{< /warning >}}

