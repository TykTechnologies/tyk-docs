---
title: "Customize Pages in Developer Portal"
date: 2025-02-10
keywords: ["Developer Portal", "Tyk", "Customization", "Pages"]
description: "How to customize pages in developer portal"
aliases:
  - /tyk-stack/tyk-developer-portal/enterprise-developer-portal/customise-enterprise-portal/full-customisation/edit-manage-page-content
---

We suggest you read the [portal concepts]({{< ref "portal/overview/concepts" >}}) first. If you've already done that, we will show you an example on how to:

- create a new layout.
- create a new template from the file system.
- create a new page from the admin dashboard.

**Prerequisites**

- Access to the file system
- Access to your Tyk Self-Managed installation

## Create a New Page using an Existing Template

Follow the example below to create a new page called “My first page” using an existing template.

{{< img src="/img/dashboard/portal-management/enterprise-portal/create-new-page1.png" alt="The pages section within the Tyk Enterprise Portal app" >}}

1. Log in to the Admin Dashboard.
2. Navigate to Pages from the side bar menu.
3. Click Add and enter the following values:

{{< img src="/img/dashboard/portal-management/enterprise-portal/add-a-content-page-using-an-existing-template.png" alt="Add a new content page" >}}

## Create a New Page

### Create the Layout File

A layout behaves like a component that can be reused to inject templates in order to avoid duplicating elements such as `<head>` and `<link>`.So let’s create one that looks like the one below.

1. From the file system navigate to `/themes/default/layouts`.
2. Create a new file named `my_layout.tmpl`.
3. Copy the code below, paste it to your new layout file and save it.

```html
<!DOCTYPE html>
<html lang="en">

 <head>

    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <meta name="description" content="">
    <meta name="author" content="">

   <title>{{ if .page}} {{.page.Title}} {{else}} Developer Portal {{end}}</title>

    <!-- Bootstrap core CSS -->
    <link href="/system/vendor/bootstrap/css/bootstrap.min.css" rel="stylesheet">
    <link href="/assets/stylesheets/fonts.css" rel="stylesheet">
    <link href="/assets/stylesheets/main.css" rel="stylesheet">

 </head>

 <body>
    {{ render "top_nav" . }}
    <div class="page-wrapper">
      <!-- Page Content -->
      {{ yield }}
   </div>


   {{ render "footer" . }}

 </body>

</html>
```
{{< note success >}}
**Note**

The above snippet is taking into account the default developer portal setup, directories and references of the appropriate styling files.

{{< /note >}}

We have also added the top and footer navigation menus for demonstration purposes, `{{ render "top_nav" . }}` and `{{ render "footer" . }}` respectively.

### Create the Template File

{{< note success >}}
**Note**

Only follow this step after creating a new template file in Section 1 above, unless you want to use an existing template.

{{< /note >}}

1. From the file system; navigate to `/themes/default/views`.
2. Create a new file (template)
3. In this example, we will keep it simple and create a couple of HTML tags. Copy and paste the following code:

```go
<div class="container">
  <h1>{{ .page.Title }}</h1>
  <p> {{ .blocks.Description.Content }}</p>
</div>
```
In this example, we use the code references in the template:
- Inside the template’s `<h1>` we use `{{ .page.Title }}` to display the page name.
- Inside the template’s `<p>` we use `{{ .blocks.Description.Content }}` to display the page content.

4. Name this `my_template.tmpl` and save it.
5. You now need to reference your new layout and template. From your Manifest file (`themes.json`) add a new key to the object that will look like this:

```json
{
  "name": "My new Template",
  "template": "my_template",
  "layout": "my_layout"
}
```
Alternatively, you can give it your preferred name but reference the template and layout names we created earlier in the manifest file.

6. Now restart your developer portal service and go through the tutorial on how to add a new page. The template dropdown within the add new page form should have a new entry called `My new Template`, so create a page that will look like this:

{{< img src="/img/dashboard/portal-management/enterprise-portal/add-page-details.png" alt="Add new page details" >}}

7. Now navigate to the path we have entered on your browser (`my-domain.io/my-first-page`) and you should be able to see your new page with the content added via the UI:

{{< img src="/img/dashboard/portal-management/enterprise-portal/my-first-page-example.png" alt="Example new UI page" >}}

Taking as a scenario our above example, let’s see a visual explaining the correlation between the different files and UI.

{{< img src="/img/dashboard/portal-management/enterprise-portal/scenario-correlation-diagram.png" alt="Scenario correlation" >}}


## Edit Page Content

Content managers or similar roles that are responsible for the content displayed on the developer portal can edit and manage pages within the **Page section** of the Developer Portal.

**Prerequisites**

- Install the Developer portal
- Log in to the portal dashboard
- Default pages available or a page created by a developer which has the custom theme linked to it

### Instructions

1. From the Pages section, open an existing page. This could be a page based on the default template or a new page that one of your developers set up when creating a new custom template.
2. Edit the page meta data. Change the name of the page if needed. Set or change the path URL if needed.

{{< img src="/img/dashboard/portal-management/enterprise-portal/page-content-edit.png" alt="Edit Portal page content" >}}

3. Edit the page content within the existing content blocks.

{{< note success >}}
**Note**

The content block name is linked to the content block name in the template html file. If this name is changed, and not reflected in the template html, the page will get an error and won’t show.

{{< /note >}}

4. Publish the page and view it from the external portal URL. If you want the page to be published and visible on the external portal, you need to change the state to Published.


