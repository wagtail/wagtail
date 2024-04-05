import io
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from django.test import TestCase

from wagtail.test.utils import WagtailTestUtils

# This test was made in order to test the Dynamic Image Serve View.
# For this test you will need to change your "mysite" in order for its home_page.html to show
# an image.
# To do that, you need to ensure that you have (it can be dynamic) serve view in the template and update
# the urls.py. Problably an addition of "image = models.ForeignKey( get_image_model(), ...)"
# field to the HomePage class will also be needed


class TestImagePresence(WagtailTestUtils, TestCase):
    def test_image_presence(self):
        # Make request to localhost
        response = requests.get("http://localhost:8000")

        # Check if the request was successful
        self.assertEqual(response.status_code, 200)

        # Parse the HTML content of the response
        soup = BeautifulSoup(response.content, "html.parser")

        # Find img elements with src="/images/"
        images = soup.find_all("img", src=lambda x: x and "/images/" in x)

        # Check if at least one image was found
        self.assertTrue(images)

        # Check for images with error (status code 500)
        for img in images:
            img_src = img.get("src")
            full_img_url = urljoin(
                "http://localhost:8000", img_src
            )  # Construct full image URL

            # Request the image
            img_response = requests.get(full_img_url, stream=True)

            # Check if the response is a properly opened file
            if img_response.ok:
                self.assertTrue(isinstance(img_response.raw, io.IOBase))
            else:
                self.fail(f"Error accessing image: {img_src}")
