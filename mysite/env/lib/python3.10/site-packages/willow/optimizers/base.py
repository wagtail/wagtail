import logging
import subprocess
from typing import ClassVar, List

logger = logging.getLogger("willow")


class OptimizerBase:
    library_name: ClassVar[str] = ""
    image_format: ClassVar[str] = ""

    class Meta:
        abstract = True

    @classmethod
    def applies_to(cls, image_format: str) -> bool:
        return image_format.lower() == cls.image_format.lower()

    @classmethod
    def get_check_library_arguments(cls) -> List[str]:
        """
        Return a list of arguments to check if the library exists.

        Note: using --help by default as that usually returns a zero exit code
        """
        return ["--help"]

    @classmethod
    def check_library(cls) -> bool:
        args = [cls.library_name] + cls.get_check_library_arguments()
        try:
            subprocess.check_output(args, stderr=subprocess.STDOUT)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False

    @classmethod
    def get_command_arguments(cls, file_path: str) -> List[str]:
        """Return a list of arguments for the given optimizer library."""
        return []

    @classmethod
    def process(cls, file_path: str):
        args = [cls.library_name] + cls.get_command_arguments(file_path)
        try:
            subprocess.check_output(args, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            logger.exception(
                "Error optimizing %s with the '%s' library with error: %s",
                file_path,
                cls.library_name,
                exc.output,
            )
