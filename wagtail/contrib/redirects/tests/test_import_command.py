import os
import tempfile
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Site

TEST_ROOT = os.path.abspath(os.path.dirname(__file__))


class TestImportCommand(TestCase):
    def test_empty_command_raises_errors(self):
        with self.assertRaises(CommandError):
            out = StringIO()
            call_command("import_redirects", stdout=out)

    def test_missing_file_raises_error(self):
        with self.assertRaisesMessage(Exception, "Missing file 'random'"):
            out = StringIO()
            call_command("import_redirects", src="random", stdout=out)

    def test_invalid_extension_raises_error(self):
        f = f"{TEST_ROOT}/files/example.yaml"

        with self.assertRaisesMessage(Exception, "Invalid format 'yaml'"):
            out = StringIO()
            call_command("import_redirects", src=f, stdout=out)

    def test_empty_file_raises_error(self):
        empty_file = tempfile.NamedTemporaryFile()

        with self.assertRaisesMessage(Exception, f"File '{empty_file.name}' is empty"):
            out = StringIO()
            call_command("import_redirects", src=empty_file.name, stdout=out)

    def test_header_are_not_imported(self):
        invalid_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        invalid_file.write("from,to")
        invalid_file.seek(0)

        out = StringIO()
        call_command(
            "import_redirects", src=invalid_file.name, stdout=out, format="csv"
        )

        self.assertEqual(Redirect.objects.count(), 0)

    def test_format_gets_picked_up_from_file_extension(self):
        f = f"{TEST_ROOT}/files/example.csv"

        out = StringIO()
        call_command("import_redirects", src=f, stdout=out)
        self.assertEqual(Redirect.objects.count(), 2)

    def test_binary_formats_are_supported(self):
        f = f"{TEST_ROOT}/files/example.xlsx"

        out = StringIO()
        call_command("import_redirects", src=f, stdout=out)
        self.assertEqual(Redirect.objects.count(), 3)

    def test_redirect_gets_imported(self):
        invalid_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        invalid_file.write("from,to\n")
        invalid_file.write("/alpha,http://omega.test/")
        invalid_file.seek(0)

        out = StringIO()
        call_command(
            "import_redirects", src=invalid_file.name, stdout=out, format="csv"
        )

        self.assertEqual(Redirect.objects.count(), 1)
        redirect = Redirect.objects.first()
        self.assertEqual(redirect.old_path, "/alpha")
        self.assertEqual(redirect.redirect_link, "http://omega.test/")
        self.assertIs(redirect.is_permanent, True)

    def test_trailing_slash_gets_stripped(self):
        invalid_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        invalid_file.write("from,to\n")
        invalid_file.write("/alpha/,http://omega.test/")
        invalid_file.seek(0)

        out = StringIO()
        call_command(
            "import_redirects", src=invalid_file.name, stdout=out, format="csv"
        )

        redirect = Redirect.objects.first()
        self.assertEqual(redirect.old_path, "/alpha")
        self.assertEqual(redirect.redirect_link, "http://omega.test/")

    def test_site_id_does_not_exist(self):
        with self.assertRaisesMessage(Exception, "Site matching query does not exist"):
            out = StringIO()
            call_command("import_redirects", src="random", site=5, stdout=out)

    def test_redirect_gets_added_to_site(self):
        invalid_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        invalid_file.write("from,to\n")
        invalid_file.write("/alpha/,http://omega.test/")
        invalid_file.seek(0)

        current_site = Site.objects.first()
        site = Site.objects.create(
            hostname="random.test", root_page=current_site.root_page
        )

        out = StringIO()
        call_command(
            "import_redirects",
            src=invalid_file.name,
            site=site.pk,
            stdout=out,
            format="csv",
        )

        redirect = Redirect.objects.first()
        self.assertEqual(redirect.old_path, "/alpha")
        self.assertEqual(redirect.redirect_link, "http://omega.test/")
        self.assertEqual(redirect.site, site)

    def test_temporary_redirect(self):
        invalid_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        invalid_file.write("from,to\n")
        invalid_file.write("/alpha/,http://omega.test/")
        invalid_file.seek(0)

        out = StringIO()
        call_command(
            "import_redirects",
            src=invalid_file.name,
            permanent=False,
            stdout=out,
            format="csv",
        )

        redirect = Redirect.objects.first()
        self.assertEqual(redirect.old_path, "/alpha")
        self.assertEqual(redirect.redirect_link, "http://omega.test/")
        self.assertIs(redirect.is_permanent, False)

    def test_duplicate_from_links_get_skipped(self):
        invalid_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        invalid_file.write("from,to\n")
        invalid_file.write("/alpha/,http://omega.test/\n")
        invalid_file.write("/alpha/,http://omega2.test/\n")
        invalid_file.seek(0)

        out = StringIO()
        call_command(
            "import_redirects",
            src=invalid_file.name,
            permanent=False,
            format="csv",
            stdout=out,
        )

        self.assertEqual(Redirect.objects.count(), 1)

    def test_non_absolute_to_links_get_skipped(self):
        invalid_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        invalid_file.write("from,to\n")
        invalid_file.write("/alpha/,/omega.test/\n")
        invalid_file.seek(0)

        out = StringIO()
        call_command(
            "import_redirects",
            src=invalid_file.name,
            permanent=False,
            stdout=out,
            format="csv",
        )

        self.assertEqual(Redirect.objects.count(), 0)
        self.assertIn("Errors: 1", out.getvalue())

    def test_from_links_are_converted_to_relative(self):
        invalid_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        invalid_file.write("from,to\n")
        invalid_file.write("http://alpha.test/alpha/,http://omega.test/\n")
        invalid_file.seek(0)

        out = StringIO()
        call_command(
            "import_redirects", src=invalid_file.name, format="csv", stdout=out
        )

        self.assertEqual(Redirect.objects.count(), 1)
        redirect = Redirect.objects.first()
        self.assertEqual(redirect.old_path, "/alpha")
        self.assertEqual(redirect.redirect_link, "http://omega.test/")

    def test_column_index_are_used(self):
        invalid_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        invalid_file.write("priority,from,year,to\n")
        invalid_file.write("5,/alpha,2020,http://omega.test/")
        invalid_file.seek(0)

        out = StringIO()
        call_command(
            "import_redirects",
            f"--src={invalid_file.name}",
            "--from=1",
            "--to=3",
            "--format=csv",
            stdout=out,
        )

        self.assertEqual(Redirect.objects.count(), 1)
        redirect = Redirect.objects.first()
        self.assertEqual(redirect.old_path, "/alpha")
        self.assertEqual(redirect.redirect_link, "http://omega.test/")
        self.assertIs(redirect.is_permanent, True)

    def test_nothing_gets_saved_on_dry_run(self):
        invalid_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        invalid_file.write("from,to\n")
        invalid_file.write("/alpha,http://omega.test/")
        invalid_file.seek(0)

        out = StringIO()
        call_command(
            "import_redirects",
            src=invalid_file.name,
            format="csv",
            dry_run=True,
            stdout=out,
        )

        self.assertEqual(Redirect.objects.count(), 0)

    @patch(
        "wagtail.contrib.redirects.management.commands.import_redirects.get_input",
        return_value="Y",
    )
    def test_successful_ask_imports_redirect(self, get_input):
        invalid_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        invalid_file.write("from,to\n")
        invalid_file.write("/alpha,http://omega.test/")
        invalid_file.seek(0)

        out = StringIO()
        call_command(
            "import_redirects",
            src=invalid_file.name,
            format="csv",
            ask=True,
            stdout=out,
        )

        self.assertEqual(Redirect.objects.count(), 1)

    @patch(
        "wagtail.contrib.redirects.management.commands.import_redirects.get_input",
        return_value="N",
    )
    def test_native_ask_imports_redirect(self, get_input):
        invalid_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        invalid_file.write("from,to\n")
        invalid_file.write("/alpha,http://omega.test/")
        invalid_file.seek(0)

        out = StringIO()
        call_command(
            "import_redirects",
            src=invalid_file.name,
            format="csv",
            ask=True,
            stdout=out,
        )

        self.assertEqual(Redirect.objects.count(), 0)

    def test_offset_parameter(self):
        invalid_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        invalid_file.write("from,to\n")
        invalid_file.write("/one,http://one.test/\n")
        invalid_file.write("/two,http://two.test/\n")
        invalid_file.write("/three,http://three.test/\n")
        invalid_file.write("/four,http://four.test/")
        invalid_file.seek(0)

        out = StringIO()
        call_command(
            "import_redirects",
            src=invalid_file.name,
            format="csv",
            offset=2,
            stdout=out,
        )

        redirects = Redirect.objects.all()

        self.assertEqual(len(redirects), 2)
        self.assertEqual(redirects[0].old_path, "/three")
        self.assertEqual(redirects[0].redirect_link, "http://three.test/")
        self.assertIs(redirects[0].is_permanent, True)
        self.assertEqual(redirects[1].old_path, "/four")
        self.assertEqual(redirects[1].redirect_link, "http://four.test/")

    def test_limit_parameter(self):
        invalid_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        invalid_file.write("from,to\n")
        invalid_file.write("/one,http://one.test/\n")
        invalid_file.write("/two,http://two.test/\n")
        invalid_file.write("/three,http://three.test/\n")
        invalid_file.write("/four,http://four.test/")
        invalid_file.seek(0)

        out = StringIO()
        call_command(
            "import_redirects",
            src=invalid_file.name,
            format="csv",
            limit=1,
            stdout=out,
        )

        redirects = Redirect.objects.all()

        self.assertEqual(len(redirects), 1)
        self.assertEqual(redirects[0].old_path, "/one")
        self.assertEqual(redirects[0].redirect_link, "http://one.test/")
        self.assertIs(redirects[0].is_permanent, True)
