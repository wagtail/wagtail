import gc
import warnings
from tempfile import SpooledTemporaryFile
from unittest.mock import patch

from django.test import TestCase

from wagtail.images.models import ClosingSpooledTemporaryFile, Filter

from .utils import Image, get_test_image_file


class ClosingSpooledTemporaryFileChunksTests(TestCase):
    def _make_file(self, data=b"hello world"):
        spooled = SpooledTemporaryFile()
        spooled.write(data)
        spooled.seek(0)
        return ClosingSpooledTemporaryFile(spooled)

    def test_chunks_yields_all_data(self):
        f = self._make_file(b"abcde")
        result = b"".join(f.chunks(chunk_size=2))
        self.assertEqual(result, b"abcde")

    def test_chunks_does_not_auto_close(self):
        f = self._make_file()
        self.assertFalse(f.file.closed)
        list(f.chunks())
        self.assertFalse(f.file.closed)

    def test_chunks_close_is_idempotent(self):
        f = self._make_file()
        list(f.chunks())
        list(f.chunks())


class ClosingSpooledTemporaryFileReadTests(TestCase):
    def _make_file(self, data=b"hello world"):
        spooled = SpooledTemporaryFile()
        spooled.write(data)
        spooled.seek(0)
        return ClosingSpooledTemporaryFile(spooled)

    def test_read_all_does_not_auto_close(self):
        f = self._make_file(b"data")
        result = f.read()
        self.assertEqual(result, b"data")
        self.assertFalse(f.file.closed)

    def test_read_in_loop_does_not_auto_close(self):
        f = self._make_file(b"abcde")
        chunks = []
        while True:
            chunk = f.read(2)
            if not chunk:
                break
            chunks.append(chunk)
        self.assertEqual(b"".join(chunks), b"abcde")
        self.assertFalse(f.file.closed)

    def test_partial_read_does_not_close(self):
        f = self._make_file(b"abcde")
        chunk = f.read(3)
        self.assertEqual(chunk, b"abc")
        self.assertFalse(f.file.closed)


class ClosingSpooledTemporaryFileDelTests(TestCase):
    def test_del_closes_unconsumed_file(self):
        spooled = SpooledTemporaryFile()
        spooled.write(b"never read")
        f = ClosingSpooledTemporaryFile(spooled)
        self.assertFalse(spooled.closed)
        del f
        gc.collect()
        self.assertTrue(spooled.closed)

    def test_no_resource_warning_on_gc(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", ResourceWarning)
            spooled = SpooledTemporaryFile()
            spooled.write(b"data")
            f = ClosingSpooledTemporaryFile(spooled)
            del f
            gc.collect()


class RenditionSpooledFileLeakTests(TestCase):
    def setUp(self):
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(colour="red"),
        )

    def test_get_rendition_no_resource_warning(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", ResourceWarning)
            self.image.get_rendition("fill-50x50")
            gc.collect()

    def test_existing_rendition_no_resource_warning(self):
        self.image.get_rendition("fill-50x50")  # warm up — create it

        with warnings.catch_warnings():
            warnings.simplefilter("error", ResourceWarning)
            self.image.get_rendition("fill-50x50")
            gc.collect()

    def test_callable_default_not_invoked_when_rendition_exists(self):
        self.image.get_rendition("fill-50x50")
        with patch.object(
            type(self.image), "create_rendition", wraps=self.image.create_rendition
        ) as mock_create:
            self.image.get_rendition("fill-50x50")

        mock_create.assert_not_called()


class GenerateRenditionFileFailureTests(TestCase):
    def setUp(self):
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(colour="blue"),
        )

    def test_spooled_file_closed_on_filter_run_failure(self):
        captured = []

        def capturing_run(img, output, source=None):
            captured.append(output)
            raise RuntimeError("simulated filter failure")

        with patch.object(Filter, "run", side_effect=capturing_run):
            with self.assertRaises(RuntimeError):
                self.image.generate_rendition_file(Filter(spec="fill-50x50"))

        self.assertEqual(len(captured), 1)
        self.assertTrue(
            captured[0].closed,
            "SpooledTemporaryFile must be closed after filter.run() raises",
        )
