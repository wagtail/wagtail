from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from django.urls import reverse
from selenium import webdriver

from .documentation_factory import DocumentationFactory
from .driver import DriverWithShortcuts

# Minimal adjustments to the settings generated by `wagtail start userguidesite`
settings = {
    "STATICFILES_FINDERS": [
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        'django.contrib.staticfiles.finders.FileSystemFinder',
    ],
    "STATICFILES_STORAGE": 'django.contrib.staticfiles.storage.StaticFilesStorage',
    "WAGTAIL_SITE_NAME": "Torchbox",
}


class TestEditorManual(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        options.add_argument("--no-sandbox")  # Bypass OS security model
        # options.add_argument("--liveserver=10.10.10.238:8000")  # Bypass OS security model

        cls.driver = DriverWithShortcuts(
            # command_executor=settings.SELENIUM_REMOTE_URL,
            desired_capabilities=webdriver.DesiredCapabilities.CHROME,
        )
        cls.driver.set_window_size(1024, 768)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    @override_settings(**settings)
    def test_intro(self):
        driver = self.driver
        base_url = self.live_server_url

        with DocumentationFactory(
                "editor_manual/intro.rst", "Introduction", driver
        ) as doc:
            driver.refresh()
            driver.get(base_url)
            doc.img("home.png")
            doc.p(
                "`Wagtail <https://wagtail.io>`_ is a new open source content management system (CMS) developed "
                "by `Torchbox <https://torchbox.com>`_. It is built on the Django framework and designed to be "
                "super easy to use for both developers and editors."
            )
            doc.p("This documentation will explain how to:")
            doc.ol(
                [
                    "navigate the main user interface of Wagtail",
                    "create pages of all different types",
                    "modify, save, publish and unpublish pages",
                    "how to set up users, and provide them with specific roles to create a publishing workflow",
                    "upload, edit and include images and documents",
                    "... and more!",
                ]
            )

        with DocumentationFactory(
                "editor_manual/getting_started.rst", "Getting started", driver
        ) as doc:
            doc.h2("The Wagtail demo site")
            doc.p(
                "The examples in this document are based on `Torchbox.com <https://torchbox.com>`_. "
                "However, the instructions are general enough as to be applicable to any Wagtail site."
            )
            doc.p(
                "For the purposes of this documentation we will be using the URL, **www.example.com**, "
                "to represent the root (homepage) of your website."
            )
            doc.h2("Logging in")
            doc.ol([
                "The first port of call for an editor is the login page for the administrator interface.",
                "Access this by adding **/admin** onto the end of your root URL (e.g. ``www.example.com/admin``).",
                "Enter your username and password and click **Sign in**.",
            ])

            username, password = "jane", "secret_password"
            get_user_model().objects.create_superuser(
                username=username,
                password=password,
                is_active=True,
                email=f"{username}@example.com",
            )
            assert get_user_model().objects.count() == 1

            driver.get(base_url + reverse("wagtailadmin_login"))
            driver.input_text("username", username)
            driver.input_text("password", password)
            doc.img("screen01_login.png", driver.find_element_by_xpath(f"//button"))
            driver.find_element_by_xpath(f"//button").click()

        with DocumentationFactory(
                "editor_manual/finding_your_way_around/index.rst", "Finding your way around", driver
        ) as doc:
            doc.p(
                "This section describes the different pages that you will see as you navigate around the CMS, "
                "and how you can find the content that you are looking for."
            )
            doc.p(
                ".. toctree::\n"
                "   :maxdepth: 3\n"
                "\n"
                "   the_dashboard\n"
                "   the_explorer_menu\n"
                "   using_search\n"
                "   the_explorer_page"
            )

        with DocumentationFactory(
                "editor_manual/finding_your_way_around/the_dashboard.rst", "The Dashboard", driver
        ) as doc:
            doc.comment("MAKE CHANGES TO INCLUDE MODERATION")
            doc.p("The Dashboard provides information on:")
            doc.ul([
                "The number of pages, images, and documents currently held in the Wagtail CMS",
                "Any pages currently awaiting moderation (if you have these privileges)",
                "Your most recently edited pages",
            ])
            doc.p("You can return to the Dashboard at any time by clicking the Wagtail logo in the top-left of the screen.")

            driver.get(base_url + reverse("wagtailadmin_home"))
            assert driver.current_url == base_url + reverse("wagtailadmin_home")
            doc.img("screen02_dashboard_editor.png")

            doc.ul([
                "Clicking the logo returns you to your Dashboard.",
                "The stats at the top of the page describe the total amount of content on the CMS (just for fun!).",
                "The *Pages awaiting moderation* table will only be displayed if you have moderator or administrator privileges",
                [
                    "Clicking the name of a page will take you to the ‘Edit page’ interface for this page.",
                    "Clicking approve or reject will either change the page status to live or return the page to draft status. An email will be sent to the creator of the page giving the result of moderation either way.",
                    "The *Parent* column tells you what the parent page of the page awaiting moderation is called. Clicking the parent page name will take you to its Edit page.",
                ]
            ])
            doc.ul([
                "The *Your most recent edits* table displays the five pages that you most recently edited.",
                "The date column displays the date that you edited the page. Hover your mouse over the date for a more exact time/date.",
                "The status column displays the current status of the page. A page will have one of three statuses:",
                [
                    "Live: Published and accessible to website visitors",
                    "Draft:  Not live on the website.",
                    "Live + Draft: A version of the page is live, but a newer version is in draft mode.",
                ],
            ])




