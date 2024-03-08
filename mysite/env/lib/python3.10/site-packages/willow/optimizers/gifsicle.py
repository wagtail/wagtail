from typing import ClassVar, List

from .base import OptimizerBase

__all__ = ["Gifsicle"]


class Gifsicle(OptimizerBase):
    """http://www.lcdf.org/gifsicle/"""

    library_name: ClassVar[str] = "gifsicle"
    image_format: ClassVar[str] = "gif"

    @classmethod
    def get_command_arguments(cls, file_path: str) -> List[str]:
        return [
            "-b",  # required parameter for the package
            "-O3",  # slowest, but produces best results
            file_path,  # the file
        ]
