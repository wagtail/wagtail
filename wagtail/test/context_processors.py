def do_not_use_static_url(request):
    def exception():
        raise Exception(
            "Do not use STATIC_URL in templates. Use the {% static %} templatetag (or {% versioned_static %} within admin templates) instead."
        )

    return {
        "STATIC_URL": lambda: exception(),
    }


CALL_COUNT = 0


def count_calls(request):
    global CALL_COUNT
    CALL_COUNT += 1
    return {}


def get_call_count():
    global CALL_COUNT
    return CALL_COUNT


def reset_call_count():
    global CALL_COUNT
    CALL_COUNT = 0
