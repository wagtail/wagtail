from typing import ClassVar, List

from .base import OptimizerBase

__all__ = ["Pngquant"]


class Pngquant(OptimizerBase):
    """https://pngquant.org/"""

    library_name: ClassVar[str] = "pngquant"
    image_format: ClassVar[str] = "png"

    @classmethod
    def get_command_arguments(
        cls, file_path: str, progressive: bool = False
    ) -> List[str]:
        return [
            "--force",  # allow overwriting existing files
            "--strip",  # remove optional metadata
            "--skip-if-larger",
            file_path,  # the file as input
            "--output",
            file_path,  # the file as output
        ]
