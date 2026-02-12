import base64
import hashlib
import hmac

from django.conf import settings
from django.utils.crypto import constant_time_compare
from django.utils.encoding import force_str


# Helper functions for migrating the Rendition.filter foreign key to the filter_spec field,
# and the corresponding reverse migration
def get_fill_filter_spec_migrations(app_name, rendition_model_name):
    def fill_filter_spec_forward(apps, schema_editor):
        # Populate Rendition.filter_spec with the spec string of the corresponding Filter object
        Rendition = apps.get_model(app_name, rendition_model_name)
        Filter = apps.get_model("wagtailimages", "Filter")

        db_alias = schema_editor.connection.alias
        for flt in Filter.objects.using(db_alias):
            renditions = Rendition.objects.using(db_alias).filter(
                filter=flt, filter_spec=""
            )
            renditions.update(filter_spec=flt.spec)

    def fill_filter_spec_reverse(apps, schema_editor):
        # Populate the Rendition.filter field with Filter objects that match the spec in the
        # Rendition's filter_spec field
        Rendition = apps.get_model(app_name, rendition_model_name)
        Filter = apps.get_model("wagtailimages", "Filter")
        db_alias = schema_editor.connection.alias

        while True:
            # repeat this process until we've confirmed that no remaining renditions exist with
            # a null 'filter' field - this minimises the possibility of new ones being inserted
            # by active server processes while the query is in progress

            # Find all distinct filter_spec strings used by renditions with a null 'filter' field
            unmatched_filter_specs = (
                Rendition.objects.using(db_alias)
                .filter(filter__isnull=True)
                .values_list("filter_spec", flat=True)
                .distinct()
            )
            if not unmatched_filter_specs:
                break

            for filter_spec in unmatched_filter_specs:
                filter, _ = Filter.objects.using(db_alias).get_or_create(
                    spec=filter_spec
                )
                Rendition.objects.using(db_alias).filter(
                    filter_spec=filter_spec
                ).update(filter=filter)

    return (fill_filter_spec_forward, fill_filter_spec_reverse)


def parse_color_string(color_string):
    """
    Parses a string a user typed into a tuple of 3 integers representing the
    red, green and blue channels respectively.

    May raise a ValueError if the string cannot be parsed.

    The colour string must be a CSS 3 or 6 digit hex code without the '#' prefix.
    """
    if len(color_string) == 3:
        r = int(color_string[0], 16) * 17
        g = int(color_string[1], 16) * 17
        b = int(color_string[2], 16) * 17
    elif len(color_string) == 6:
        r = int(color_string[0:2], 16)
        g = int(color_string[2:4], 16)
        b = int(color_string[4:6], 16)
    else:
        raise ValueError("Color string must be either 3 or 6 hexadecimal digits long")

    return r, g, b


def generate_signature(image_id, filter_spec, key=None):
    if key is None:
        key = settings.SECRET_KEY

    # Key must be a bytes object
    if isinstance(key, str):
        key = key.encode()

    # Based on libthumbor hmac generation
    # https://github.com/thumbor/libthumbor/blob/b19dc58cf84787e08c8e397ab322e86268bb4345/libthumbor/crypto.py#L50
    url = f"{image_id}/{filter_spec}/"
    return force_str(
        base64.urlsafe_b64encode(hmac.new(key, url.encode(), hashlib.sha1).digest())
    )


def verify_signature(signature, image_id, filter_spec, key=None):
    return constant_time_compare(
        signature, generate_signature(image_id, filter_spec, key=key)
    )


def find_image_duplicates(image, user, permission_policy):
    """
    Finds all the duplicates of a given image.
    To keep things simple, two images are considered to be duplicates if they have the same `file_hash` value.
    This function also ensures that the `user` can choose one of the duplicate images returned (if any).
    """

    instances = permission_policy.instances_user_has_permission_for(user, "choose")
    return instances.exclude(pk=image.pk).filter(file_hash=image.file_hash)


def to_svg_safe_spec(filter_specs):
    """
    Remove any directives that would require an SVG to be rasterised
    """
    if isinstance(filter_specs, str):
        filter_specs = filter_specs.split("|")

    svg_preserving_specs = [
        "max",
        "min",
        "width",
        "height",
        "scale",
        "fill",
        "original",
    ]

    # Keep only safe operations and remove preserve-svg
    safe_specs = [
        x
        for x in filter_specs
        if any(x.startswith(prefix) for prefix in svg_preserving_specs)
    ]

    # If no safe operations remain, use 'original'
    if not safe_specs:
        return "original"

    return "|".join(safe_specs)


def get_allowed_image_extensions():
    return getattr(
        settings,
        "WAGTAILIMAGES_EXTENSIONS",
        ["avif", "gif", "jpg", "jpeg", "png", "webp"],
    )


def get_accept_attributes():
    allowed_image_extensions = get_allowed_image_extensions()
    accept_attrs = "image/*"
    if "heic" in allowed_image_extensions:
        accept_attrs += ", image/heic"
    if "avif" in allowed_image_extensions:
        accept_attrs += ", image/avif"

    return accept_attrs
