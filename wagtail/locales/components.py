LOCALE_COMPONENTS = []


def get_locale_components():
    return LOCALE_COMPONENTS


def register_locale_component(model):
    if model not in LOCALE_COMPONENTS:
        LOCALE_COMPONENTS.append(model)
        LOCALE_COMPONENTS.sort(key=lambda x: x._meta.verbose_name)

    return model
