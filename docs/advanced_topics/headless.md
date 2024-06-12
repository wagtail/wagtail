(headless)=

# Headless support

```{contents}
---
local:
depth: 3
---
```

Wagtail has good support for headless sites, but there are some issues developers should take into account when using Wagtail as a headless CMS.

(headless_api)=

## API considerations

There are generally two popular options for API when using Wagtail as a headless CMS, REST and GraphQL.

### REST

REST (or representational state transfer) was introduced in 2000 as a simpler approach to machine-to-machine communication using the HTTP protocol. Since REST was introduced, RESTful APIs have proliferated across the web to the point where they're essentially the default standard for modern APIs. Many headless content management systems use either RESTful architecture or GraphQL for their APIs. Both options work with Headless Wagtail, so let's explore the upsides and downsides of choosing REST.

#### Upsides of a REST API

* Requests can be sent using common software like cURL or through web browsers.
* The REST standards are open source and relatively simple to learn.
* REST uses standard HTTP actions like GET, POST, and PUT.
* REST operations require less bandwidth then other comparable technologies (such as SOAP).
* REST is stateless on the server-side, so each request is processed independently.
* Caching is manageable with REST.
* REST is more common currently and there are many more tools available to support REST.
* The REST API is a native feature of Wagtail with some functionality already built in.

#### Downsides of a REST API

* Sometimes, multiple queries are required to return the necessary data.
* REST isn't always efficient if a query requires access to multiple endpoints.
* Requests to REST APIs can return extra data that's not needed.
* REST depends on fixed data structures that can be somewhat difficult to update.

```{note}
If you don't want to use Wagtail's built-in REST API, you can build your own using the Django REST framework https://www.django-rest-framework.org/. Remember, Wagtail is just Django!
```

#### REST Resources

* [Official Wagtail documentation on building a public-facing API](https://docs.wagtail.org/en/stable/advanced_topics/api/index.html)
* Wagtail API tutorial from [LearnWagtail.com](https://learnwagtail.com/tutorials/how-to-enable-the-v2-api-to-create-a-headless-cms/)

### GraphQL

GraphQL is a newer API technology than REST. Unlike REST, GraphQL isn't an architecture; it's a data query language that helps simplify API requests. GraphQL was developed by Facebook (now Meta) and open sourced in 2015. It's a newer technology that was designed to provide more flexibility and efficiency than REST. Besides REST, GraphQL is currently the only other API technology that is recommended for Headless Wagtail. Let's have a look at the current upsides and downsides of choosing GraphQL.

#### Upsides of GraphQL

* Changes can be made more rapidly on the client-side of a project without substantial backend updates.
* Queries can be more precise and efficient without over- or under-fetching data.
* You can use fewer queries to retrieve data that would require multiple endpoints in REST.
* GraphQL APIs use fewer resources with fewer queries.
* GraphQL provides options for analytics and performance monitoring.

#### Downsides of GraphQL

* GraphQL is not natively supported in Wagtail.
* You will need to install a library package to use GraphQL.
* There are currently fewer tools and resources available for supporting GraphQL.
* Fewer developers are familiar with GraphQL.

GraphQL libraries compatible with Wagtail

* [wagtail-grapple](https://github.com/GrappleGQL/wagtail-grapple) by GrappleGQL
* [strawberry-wagtail](https://github.com/patrick91/strawberry-wagtail) by Patrick Arminio
