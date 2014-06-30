custom_blocks_registry = {}


class BaseBlock(object):
    @classmethod
    def get_name(cls):
        # return a string name used within the ST plugin
        name = getattr(cls, 'name', None)
        if name:
            return name
        else:
            raise NotImplementedError('subclasses of BaseBlock must provide a get_name() method or define a name attribute')

    @classmethod
    def get_template(cls): 
        # return template file name, so the template finder can find it
        template = getattr(cls, 'template', None)
        if template:
            return template
        else:
            raise NotImplementedError('subclasses of BaseBlock must provide a get_template() method or define a template attribute')

    @classmethod
    def get_js(cls): 
        # return static file location, relative to static path so the static finder can find it
        js = getattr(cls, 'js', None)
        if js:
            return js
        else:
            raise NotImplementedError('subclasses of BaseBlock must provide a get_js() method or define a js attribute')


def register_block(block, name=None):
    if name is None:
        name = block.get_name()

    if not issubclass(block, BaseBlock):
        raise TypeError

    custom_blocks_registry[name] = block