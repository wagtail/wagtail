from typing import ClassVar, List

from .base import OptimizerBase

__all__ = ["Cwebp"]


class Cwebp(OptimizerBase):
    """https://developers.google.com/speed/webp/docs/cwebp"""

    library_name: ClassVar[str] = "cwebp"
    image_format: ClassVar[str] = "webp"

    @classmethod
    def get_check_library_arguments(cls) -> List[str]:
        # running just cwebp gives basic infor and returns a zero exit code
        return []

    @classmethod
    def get_command_arguments(
        cls, file_path: str, progressive: bool = False
    ) -> List[str]:
        return [
            "-m",
            "6",  # inspect all encoding possibilities for best file size
            "-mt",  # use multithreading if possible
            "-pass",
            "10",  # max number of passes
            "-q",
            "75",  # compression factor. 100 produces the highest quality.
            file_path,
            "-o",
            file_path,
        ]
