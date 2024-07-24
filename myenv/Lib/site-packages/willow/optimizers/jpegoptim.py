from typing import ClassVar, List

from .base import OptimizerBase

__all__ = ["Jpegoptim"]


class Jpegoptim(OptimizerBase):
    """https://github.com/tjko/jpegoptim"""

    library_name: ClassVar[str] = "jpegoptim"
    image_format: ClassVar[str] = "jpeg"

    @classmethod
    def get_command_arguments(cls, file_path: str) -> List[str]:
        return [
            "--strip-all",  # strip out all text information like comments and EXIF data
            "--max=85",  # set maximum quality
            "--all-progressive",  # make the resulting image progressive
            file_path,
        ]
