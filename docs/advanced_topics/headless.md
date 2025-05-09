(headless)=

# Headless support

Wagtail has good support for headless sites, but there are some limitations developers should take into account when using Wagtail as a headless CMS.
This page covers most topics related to headless sites, and tries to identify where you might run into issues using ✅ (good support), ⚠️ (workarounds needed or incomplete support) and 🛑 (lacking support).

Wagtail maintains a current list of issues tagged with #headless on [GitHub](https://github.com/wagtail/wagtail/issues?q=is%3Aopen+is%3Aissue+label%3AHeadless)

(headless_api)=

## API

There are generally two popular options for API when using Wagtail as a headless CMS, REST and GraphQL.

### ✅ REST

REST (or REpresentational State Transfer) was introduced in 2000 as a simpler approach to machine-to-machine communication using the HTTP protocol. Since REST was introduced, RESTful APIs have proliferated across the web to the point where they're essentially the default standard for modern APIs. Many headless content management systems use either RESTful architecture or GraphQL for their APIs. Both options work with headless Wagtail, so let's explore the upsides and downsides of choosing REST.

#### Upsides of a REST API

-   Requests can be sent using common software like cURL or through web browsers.
-   The REST standards are open source and relatively simple to learn.
-   REST uses standard HTTP actions like GET, POST, and PUT.
-   REST operations require less bandwidth then other comparable technologies (such as SOAP).
-   REST is stateless on the server-side, so each request is processed independently.
-   Caching is manageable with REST.
-   REST is more common currently and there are many more tools available to support REST.
-   The REST API is a native feature of Wagtail with some functionality already built in.

#### Downsides of a REST API

-   Sometimes, multiple queries are required to return the necessary data.
-   REST isn't always efficient if a query requires access to multiple endpoints.
-   Requests to REST APIs can return extra data that's not needed.
-   REST depends on fixed data structures that can be somewhat difficult to update.

```{note}
If you don't want to use Wagtail's built-in REST API, you can build your own using the [Django REST framework](https://www.django-rest-framework.org/). Remember, Wagtail is just Django.
```

### ✅ GraphQL

GraphQL is a newer API technology than REST. Unlike REST, GraphQL isn't an architecture; it's a data query language that helps simplify API requests. GraphQL was developed by Facebook (now Meta) and open sourced in 2015. It's a newer technology that was designed to provide more flexibility and efficiency than REST. Besides REST, GraphQL is currently the only other API technology that is recommended for headless Wagtail. Let's have a look at the current upsides and downsides of choosing GraphQL.

#### Upsides of GraphQL

-   Changes can be made more rapidly on the client-side of a project without substantial backend updates.
-   Queries can be more precise and efficient without over- or under-fetching data.
-   You can use fewer queries to retrieve data that would require multiple endpoints in REST.
-   GraphQL APIs use fewer resources with fewer queries.
-   GraphQL provides options for analytics and performance monitoring.

#### Downsides of GraphQL

-   GraphQL is not natively supported in Wagtail.
-   You will need to install a library package to use GraphQL.
-   There are currently fewer tools and resources available for supporting GraphQL.
-   Fewer developers are familiar with GraphQL.
-   GraphQL can introduce additional performance and security considerations due to its flexibility.

#### GraphQL libraries compatible with Wagtail

-   [wagtail-grapple](https://github.com/torchbox/wagtail-grapple) by Torchbox
-   [strawberry-wagtail](https://github.com/patrick91/strawberry-wagtail) by Patrick Arminio

## Functionality

### ⚠️ Page preview

Previews need a workaround currently.

There currently isn’t a way to request a draft version of a page using the public API. We typically recommend [wagtail-headless-preview](https://github.com/torchbox/wagtail-headless-preview), a mature and widely used third-party package.

When autosave is released in Wagtail, generating previews will likely be less of an obstacle since the API would be serving up the latest changes in all circumstances. This is can be achieved using a [workaround](https://github.com/cfpb/wagtail-sharing/pull/47).

### ⚠️ Images

Additional image considerations are needed for headless Wagtail.

On traditional sites, Wagtail has a template tag that makes it easy for a frontend developer to request an image of a particular size. Currently, the Wagtail API provides two solutions:

-   Add an [ImageRenditionField](api_v2_images) to the model, that allows an image in a particular placement on a page to be requested at a pre-defined size. This is the approach we recommend in most cases.
-   Use the [dynamic image serve](using_images_outside_wagtail) view, which allows any image to be rendered at any size. Note that this approach may require extra work, since a key is required and you'll need a secure way to pass the key back and forth. Without this, there's a higher risk of crashing your site, by an attacker requesting the same image in millions of subtly different ways.

Neither of these solutions are easy for a frontend developer. They may not have the access or skills to add an `ImageRenditionField`, and crafting a URL to the dynamic image serve view is tricky because it needs to be signed and there currently isn’t a library or code snippet to do this from JavaScript. Hashes also need to be generated and the current JS version is complex.

### ⚠️ Page URL routing

Headless Wagtail requires different routing.

A different approach to routing is needed for headless Wagtail projects. Unlike the traditional routing for Wagtail, the URL patterns on a headless site are usually configured in the frontend framework (such as [Next.js](https://areweheadlessyet.wagtail.org/nextjs/) or [Gatsby](https://areweheadlessyet.wagtail.org/gatsby/)). Wagtail, by default, resolves URLs to pages using their slugs and location in the page tree.

Because of this default, the "View Live" links in the administration view of Wagtail may resolve to the wrong URL if the URL patterns configured in the frontend framework don't match the page structure. If rich text is rendered server-side, this will also affect any internal links in rich text fields.

The current recommended approach to routing on a headless Wagtail project is to stick with using the Wagtail routes rather than creating custom routes. Creating custom routes will require more frequent updates and maintenance.

Routes need to be built each time a new site is created and we'd like better documentation to explain this process. One long-term solution for supporting routing in headless Wagtail may be to manage it through a JS library or a plugin.

### ⚠️ Rich text

There are broadly two approaches to handling rich text in headless Wagtail:

#### Rendering on the backend

Wagtail stores rich text internally in a HTML-like format with some custom elements to support internal page links and image embeds. On a traditional Wagtail site, those custom tags are converted into standard HTML, but this doesn't happen in the built-in API. The API returns unprocessed rich text content, which means that users need to either parse the HTML on the frontend and convert the custom tags or they need implement a custom serializer to render the RichText fields on the backend. Currently, [wagtail-grapple](https://github.com/GrappleGQL/wagtail-grapple) pre-renders the HTML. So one solution could be to update the built-in API to also pre-render the HTML.

Rendering on the backend is currently the easier approach to user for managing rich text. Note that using this approach requires page URLs to follow Wagtail's conventions, so custom routing isn't possible without some complex configuration.

#### Rendering on the frontend

Pre-rendering the HTML on the backend may be more convenient if you're happy with the way Wagtail renders it, but it's still difficult to customize the rendering on the frontend. Other headless CMSs provide Rich Text as a sequence of blocks in JSON format. This approach makes it easier to customize the rendering of the blocks without having to find a way to parse the HTML fragment.

This approach is currently the harder approach for managing rich text.

### 🛑 Multi-site support

Multi-site works differently in headless Wagtail.

The notion of a “site” is different for headless Wagtail. In traditional Wagtail, the domain or port of a Wagtail site are where Wagtail will serve content and the location the end user visits to find the site.

But in headless Wagtail, the domain or port that the end user uses and domain or port that Wagtail serves content on will be different. For example, the end user may visit **www.wagtail.org**, and the website could be a Next.js app that queries a Wagtail instance running at **api.wagtail.org**.

Wagtail’s current API implementation will check the host header and port to find the site so that it only returns pages under that site. This means that your site record must be set to **api.wagtail.org**. However, when Wagtail generates URLs, these URLs need to be generated for **www.wagtail.org**.

The Wagtail API only allows requests from one site at a time to make sure any site listings are isolated from other sites by default. But the API could be improved in the following ways:

-   Allow the site to be specified in the API request.
-   Allow all pages across all sites to be queried on an opt-in basis.

With these approaches, the site record in the Wagtail admin of headless Wagtail would be set to the domain or port that the end user sees so URLs could be reversed correctly. All API requests would specify the site as a GET parameter.

### 🛑 Form submissions

There’s currently no official API for a headless site to use to submit data to a Wagtail form.

### 🛑 Password-protected pages

There currently isn’t a way to view a password-protected page from a headless frontend. The API currently excludes all password-protected pages from queries.

## Frontend

There are a few options to build your frontend for Wagtail.

### ⚠️ Next.js

Next.js is a [popular open source JavaScript framework](https://nextjs.org/) you can choose for building the frontend of your headless Wagtail website.

There's no specific support for Next.js in headless Wagtail, but you could take a look at Wagtail's self-paced [guide](https://github.com/wagtail/nextjs-loves-wagtail) to Next.js and Wagtail or projects using Wagtail and Next.js on [Github](https://github.com/search?q=next.js+wagtail), for inspiration and exploration.

### ⚠️ Nuxt.js

Nuxt.js is an [open source JavaScript framework](https://nuxtjs.org/) you can use to build a frontend for your headless Wagtail project. Several high profile sites run a combination of Wagtail and Nuxt.js, including NASA's [Jet Propulsion Laboratory](https://torchbox.com/blog/nasa-jpl-launches-on-wagtail/). While there is currently no specific support for Nuxt.js, Wagtail's built-in API makes this a straightforward option. Several projects are available on [GitHub](https://github.com/search?q=nuxt+wagtail) for inspiration and exploration.

### ⚠️ Gatsby

Gatsby is a frontend JavaScript framework for generating static websites that you could use for your headless Wagtail site.

There is currently no specific support for Gatsby in headless Wagtail. There is a plugin available called gatsby-source-wagtail you can use for connecting Wagtail to a Gatsby frontend. Choosing to use that plugin means committing to using a GraphQL library for your API, since it only works with the wagtail-grapple library.

## Supporting platforms

There are many platforms you can use to host your frontend site, here are some that have been used in combination with Wagtail.

### ⚠️ Vercel

Vercel is a frontend platform for developer teams that uses Next.js.

Currently, there is no plugin available to use Vercel with headless Wagtail. Most of the backend server rendering will generate new content anyway, so you can proceed without a plugin if you want.

### ✅ Netlify

Netlify is a [platform for publishing static websites](https://www.netlify.com/) that can be used to create a frontend for your headless Wagtail site.

There is a plugin available currently that automatically pings Netlify to build a new version of your headless Wagtail site every time you publish called [wagtail-netify](https://github.com/tomdyson/wagtail-netlify).

## Additional resources

-   [Official Wagtail documentation on building a public-facing API](api)
-   Wagtail API tutorial from [LearnWagtail.com](https://learnwagtail.com/tutorials/how-to-enable-the-v2-api-to-create-a-headless-cms/)
-   [Using Wagtail, NuxtJS and Vuetify to build a fast and secure static site](https://www.nurseadvance.com/articles/using-wagtail-nuxtjs-and-vuetify-build-fast-and-secure-static-site/)
-   [Going Headless with Wagtail, Nuxt.js and GraphQL (PDF)](https://dataverse.jpl.nasa.gov/dataset.xhtml?persistentId=hdl:2014/54119&version=2.0)
