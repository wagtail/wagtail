from io import StringIO
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.handlers.base import BaseHandler
from django.core.handlers.wsgi import WSGIRequest
from django.http.request import validate_host
from django.template.response import TemplateResponse
from django.utils.cache import patch_cache_control
from django.utils.translation import gettext_lazy as _


class PreviewableMixin:
    """A mixin that allows a model to have previews."""

    def make_preview_request(
        self, original_request=None, preview_mode=None, extra_request_attrs=None
    ):
        """
        Simulate a request to this object, by constructing a fake HttpRequest object that is (as far
        as possible) representative of a real request to this object's front-end URL, and invoking
        serve_preview with that request (and the given preview_mode).

        Used for previewing / moderation and any other place where we
        want to display a view of this object in the admin interface without going through the regular
        page routing logic.

        If you pass in a real request object as original_request, additional information (e.g. client IP, cookies)
        will be included in the dummy request.
        """
        dummy_meta = self._get_dummy_headers(original_request)
        request = WSGIRequest(dummy_meta)

        # Add a flag to let middleware know that this is a dummy request.
        request.is_dummy = True

        if extra_request_attrs:
            for k, v in extra_request_attrs.items():
                setattr(request, k, v)

        obj = self

        # Build a custom django.core.handlers.BaseHandler subclass that invokes serve_preview as
        # the eventual view function called at the end of the middleware chain, rather than going
        # through the URL resolver
        class Handler(BaseHandler):
            def _get_response(self, request):
                request.is_preview = True
                request.preview_mode = preview_mode
                response = obj.serve_preview(request, preview_mode)
                if hasattr(response, "render") and callable(response.render):
                    response = response.render()
                patch_cache_control(response, private=True)
                return response

        # Invoke this custom handler.
        handler = Handler()
        handler.load_middleware()
        return handler.get_response(request)

    def _get_fallback_hostname(self):
        """
        Return a hostname that can be used on preview requests when the object has no
        routable URL, or the real hostname is not valid according to ALLOWED_HOSTS.
        """
        try:
            hostname = settings.ALLOWED_HOSTS[0]
        except IndexError:
            # Django disallows empty ALLOWED_HOSTS outright when DEBUG=False, so we must
            # have DEBUG=True. In this mode Django allows localhost amongst others.
            return "localhost"

        if hostname == "*":
            # Any hostname is allowed
            return "localhost"

        # Hostnames beginning with a dot are domain wildcards such as ".example.com" -
        # these allow example.com itself, so just strip the dot
        return hostname.lstrip(".")

    def _get_dummy_headers(self, original_request=None):
        """
        Return a dict of META information to be included in a faked HttpRequest object to pass to
        serve_preview.
        """
        url = self._get_dummy_header_url(original_request)
        if url:
            url_info = urlsplit(url)
            hostname = url_info.hostname
            if not validate_host(
                hostname,
                settings.ALLOWED_HOSTS or [".localhost", "127.0.0.1", "[::1]"],
            ):
                # The hostname is not valid according to ALLOWED_HOSTS - use a fallback
                hostname = self._get_fallback_hostname()

            path = url_info.path
            port = url_info.port or (443 if url_info.scheme == "https" else 80)
            scheme = url_info.scheme
        else:
            # Cannot determine a URL to this object - cobble together an arbitrary valid one
            hostname = self._get_fallback_hostname()
            path = "/"
            port = 80
            scheme = "http"

        http_host = hostname
        if port != (443 if scheme == "https" else 80):
            http_host = f"{http_host}:{port}"
        dummy_values = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": path,
            "SERVER_NAME": hostname,
            "SERVER_PORT": port,
            "SERVER_PROTOCOL": "HTTP/1.1",
            "HTTP_HOST": http_host,
            "wsgi.version": (1, 0),
            "wsgi.input": StringIO(),
            "wsgi.errors": StringIO(),
            "wsgi.url_scheme": scheme,
            "wsgi.multithread": True,
            "wsgi.multiprocess": True,
            "wsgi.run_once": False,
        }

        # Add important values from the original request object, if it was provided.
        HEADERS_FROM_ORIGINAL_REQUEST = [
            "REMOTE_ADDR",
            "HTTP_X_FORWARDED_FOR",
            "HTTP_COOKIE",
            "HTTP_USER_AGENT",
            "HTTP_AUTHORIZATION",
            "wsgi.version",
            "wsgi.multithread",
            "wsgi.multiprocess",
            "wsgi.run_once",
        ]
        if settings.SECURE_PROXY_SSL_HEADER:
            HEADERS_FROM_ORIGINAL_REQUEST.append(settings.SECURE_PROXY_SSL_HEADER[0])
        if original_request:
            for header in HEADERS_FROM_ORIGINAL_REQUEST:
                if header in original_request.META:
                    dummy_values[header] = original_request.META[header]

        return dummy_values

    def _get_dummy_header_url(self, original_request=None):
        """
        Return the URL that _get_dummy_headers() should use to set META headers
        for the faked HttpRequest.
        """
        if url := self.full_url:
            return url
        # If no full_url is defined, try to use the original request's URL
        # to build a dummy request so that we get the correct scheme and host.
        if original_request:
            return original_request.build_absolute_uri("/")

    def get_full_url(self):
        return None

    full_url = property(get_full_url)

    DEFAULT_PREVIEW_MODES = [("", _("Default"))]
    DEFAULT_PREVIEW_SIZES = [
        {
            "name": "mobile",
            "icon": "mobile-alt",
            "device_width": 375,
            "label": _("Preview in mobile size"),
        },
        {
            "name": "tablet",
            "icon": "tablet-alt",
            "device_width": 768,
            "label": _("Preview in tablet size"),
        },
        {
            "name": "desktop",
            "icon": "desktop",
            "device_width": 1280,
            "label": _("Preview in desktop size"),
        },
    ]

    @property
    def preview_modes(self):
        """
        A list of ``(internal_name, display_name)`` tuples for the modes in which
        this object can be displayed for preview/moderation purposes. Ordinarily an object
        will only have one display mode, but subclasses can override this -
        for example, a page containing a form might have a default view of the form,
        and a post-submission 'thank you' page.
        Set to ``[]`` to completely disable previewing for this model.
        """
        return PreviewableMixin.DEFAULT_PREVIEW_MODES

    @property
    def default_preview_mode(self):
        """
        The default preview mode to use in live preview.
        This default is also used in areas that do not give the user the option of selecting a
        mode explicitly, e.g. in the moderator approval workflow.
        If ``preview_modes`` is empty, an ``IndexError`` will be raised.
        """
        return self.preview_modes[0][0]

    @property
    def preview_sizes(self):
        """
        A list of dictionaries, each representing a preview size option for this object.
        Override this property to customize the preview sizes.
        Each dictionary in the list should include the following keys:

        - ``name``: A string representing the internal name of the preview size.
        - ``icon``: A string specifying the icon's name for the preview size button.
        - ``device_width``: An integer indicating the device's width in pixels.
        - ``label``: A string for the aria label on the preview size button.

        .. code-block:: python

            @property
            def preview_sizes(self):
                return [
                    {
                        "name": "mobile",
                        "icon": "mobile-icon",
                        "device_width": 320,
                        "label": "Preview in mobile size"
                    },
                    # Add more preview size dictionaries as needed.
                ]
        """
        return PreviewableMixin.DEFAULT_PREVIEW_SIZES

    @property
    def default_preview_size(self):
        """
        The default preview size name to use in live preview.
        Defaults to ``"mobile"``, which is the first one defined in ``preview_sizes``.
        If ``preview_sizes`` is empty, an ``IndexError`` will be raised.
        """
        return self.preview_sizes[0]["name"]

    def is_previewable(self):
        """Returns ``True`` if at least one preview mode is specified in ``preview_modes``."""
        return bool(self.preview_modes)

    def serve_preview(self, request, mode_name):
        """
        Returns an HTTP response for use in object previews.

        This method can be overridden to implement custom rendering and/or
        routing logic.

        Any templates rendered during this process should use the ``request``
        object passed here - this ensures that ``request.user`` and other
        properties are set appropriately for the wagtail user bar to be
        displayed/hidden. This request will always be a GET.
        """
        return TemplateResponse(
            request,
            self.get_preview_template(request, mode_name),
            self.get_preview_context(request, mode_name),
        )

    def get_preview_context(self, request, mode_name):
        """
        Returns a context dictionary for use in templates for previewing this object.

        By default, this returns a dictionary containing the ``request`` and
        and the ``object`` itself.
        """
        return {"object": self, "request": request}

    def get_preview_template(self, request, mode_name):
        """
        Returns a template to be used when previewing this object.

        Subclasses of ``PreviewableMixin`` must override this method to return the
        template name to be used in the preview. Alternatively, subclasses can also
        override the ``serve_preview`` method to completely customise the preview
        rendering logic.
        """
        raise ImproperlyConfigured(
            "%s (subclass of PreviewableMixin) must override get_preview_template or serve_preview"
            % type(self).__name__
        )
