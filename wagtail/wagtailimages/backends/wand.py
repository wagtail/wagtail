from .base import ImageBackend


class WandBackend(ImageBackend):
    def __init__(self, image):
        self.image = image

    def to_buffer(self):
        return 'RGB', self.image.size, self.image.make_blob('RGB')

# DOESNT WORK. SEE: https://github.com/dahlia/wand/issues/123
#    @classmethod
#    def from_buffer(cls, buf):
#        mode, size, data = buf
#        return cls(Image(blob=data, format=mode, width=size[0], height=size[1]))

    @classmethod
    def from_file(cls, f):
        wand_image = cls.get_wand_image()
        wand_api = cls.get_wand_api()

        f.seek(0)

        image = wand_image.Image(file=f)
        image.wand = wand_api.library.MagickCoalesceImages(image.wand)
        return cls(image)

    @classmethod
    def get_wand_image(cls):
        import wand.image
        return wand.image

    @classmethod
    def get_wand_api(cls):    
        import wand.api
        return wand.api

    @classmethod
    def check(cls):
        cls.get_wand_image()
        cls.get_wand_api()


@WandBackend.register_operation('get_size')
def wand_get_size(backend):
    return backend.image.size


@WandBackend.register_operation('resize')
def wand_resize(backend, width, height):
    backend.image.resize(width, height)


@WandBackend.register_operation('crop')
def wand_crop(backend, left, top, right, bottom):
    backend.image.crop(left=left, top=top, right=right, bottom=bottom)
