(private_pages)=

# Private pages

Users with publish permission on a page can set it to be private by clicking the 'Privacy' control in the top right corner of the page explorer or editing interface. This sets a restriction on who is allowed to view the page and its sub-pages. Several different kinds of restriction are available:

-   **Accessible to logged-in users:** The user must log in to view the page. All user accounts are granted access, regardless of permission level.
-   **Accessible with the following password:** The user must enter the given password to view the page. This is appropriate for situations where you want to share a page with a trusted group of people, but giving them individual user accounts would be overkill. The same password is shared between all users, and this works independently of any user accounts that exist on the site.
-   **Accessible to users in specific groups:** The user must be logged in, and a member of one or more of the specified groups, in order to view the page.

Similarly, documents can be made private by placing them in a collection with appropriate privacy settings (see: [](image_document_permissions)).

Private pages and documents work on Wagtail out of the box - the site implementer does not need to do anything to set them up. However, the default "log in" and "password required" forms are only bare-bones HTML pages, and site implementers may wish to replace them with a page customised to their site design.

(login_page)=

## Setting up a login page

The basic login page can be customised by setting `WAGTAIL_FRONTEND_LOGIN_TEMPLATE` to the path of a template you wish to use:

```python
WAGTAIL_FRONTEND_LOGIN_TEMPLATE = 'myapp/login.html'
```

Wagtail uses Django's standard `django.contrib.auth.views.LoginView` view here, and so the context variables available on the template are as detailed in [Django's login view documentation](django.contrib.auth.views.LoginView).

If the stock Django login view is not suitable - for example, you wish to use an external authentication system, or you are integrating Wagtail into an existing Django site that already has a working login view - you can specify the URL of the login view via the `WAGTAIL_FRONTEND_LOGIN_URL` setting:

```python
WAGTAIL_FRONTEND_LOGIN_URL = '/accounts/login/'
```

To integrate Wagtail into a Django site with an existing login mechanism, setting `WAGTAIL_FRONTEND_LOGIN_URL = LOGIN_URL` will usually be sufficient.

## Setting up a global "password required" page

By setting `PASSWORD_REQUIRED_TEMPLATE` in your Django settings file, you can specify the path of a template which will be used for all "password required" forms on the site (except for page types that specifically override it - see below):

```python
PASSWORD_REQUIRED_TEMPLATE = 'myapp/password_required.html'
```

This template will receive the same set of context variables that the blocked page would pass to its own template via `get_context()` - including `page` to refer to the page object itself - plus the following additional variables (which override any of the page's own context variables of the same name):

-   **form** - A Django form object for the password prompt; this will contain a field named `password` as its only visible field. A number of hidden fields may also be present, so the page must loop over `form.hidden_fields` if not using one of Django's rendering helpers such as `form.as_p`.
-   **action_url** - The URL that the password form should be submitted to, as a POST request.

A basic template suitable for use as `PASSWORD_REQUIRED_TEMPLATE` might look like this:

```html+django
<!DOCTYPE HTML>
<html>
    <head>
        <title>Password required</title>
    </head>
    <body>
        <h1>Password required</h1>
        <p>You need a password to access this page.</p>
        <form action="{{ action_url }}" method="POST">
            {% csrf_token %}

            {{ form.non_field_errors }}

            <div>
                {{ form.password.errors }}
                {{ form.password.label_tag }}
                {{ form.password }}
            </div>

            {% for field in form.hidden_fields %}
                {{ field }}
            {% endfor %}
            <input type="submit" value="Continue" />
        </form>
    </body>
</html>
```

Password restrictions on documents use a separate template, specified through the setting `DOCUMENT_PASSWORD_REQUIRED_TEMPLATE`; this template also receives the context variables `form` and `action_url` as described above.

## Setting a "password required" page for a specific page type

The attribute `password_required_template` can be defined on a page model to use a custom template for the "password required" view, for that page type only. For example, if a site had a page type for displaying embedded videos along with a description, it might choose to use a custom "password required" template that displays the video description as usual, but shows the password form in place of the video embed.

```python
class VideoPage(Page):
    ...

    password_required_template = 'video/password_required.html'
```
