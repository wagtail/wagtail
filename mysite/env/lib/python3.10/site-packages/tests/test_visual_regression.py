from http import server
import pathlib
import threading

import percy
from selenium import webdriver
from selenium.webdriver.firefox import options as firefox_options


BASE_DIR = pathlib.Path(__file__).parent.parent.resolve()
DOCS_BUILD_DIR = BASE_DIR / "docs/_build/html/"


class DocsHTTPRequestHandler(server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS_BUILD_DIR), **kwargs)


def main():
    if not DOCS_BUILD_DIR.exists():
        print(
            "No docs build directory found. "
            "Did you forget to build the development docs?"
        )
        exit(1)

    handler_class = DocsHTTPRequestHandler
    server_address = ('127.0.0.1', 8000)

    httpd = server.HTTPServer(server_address, handler_class)

    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.start()

    print("Server thread running. Starting client requests...")
    options = firefox_options.Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)

    def take_snapshot(url, title):
        print(f"Taking snapshot of {title} at: {url}")
        driver.get(url)
        driver.implicitly_wait(2)
        percy.percy_snapshot(driver, title)

    pages = [
        ("http://localhost:8000", "Homepage"),
        ("http://localhost:8000/examples/admonitions.html", "Admonitions"),
        ("http://localhost:8000/examples/autodoc.html", "Autodoc"),
        ("http://localhost:8000/examples/code-blocks.html", "Code blocks"),
        ("http://localhost:8000/examples/headings.html", "Headings"),
        ("http://localhost:8000/examples/images.html", "Images"),
        ("http://localhost:8000/examples/links.html", "Links"),
        ("http://localhost:8000/examples/lists.html", "Lists"),
        ("http://localhost:8000/examples/paragraphs.html", "Paragraphs"),
        ("http://localhost:8000/examples/rst-page.html", "Restructured Text"),
    ]

    for page in pages:
        take_snapshot(page[0], page[1])

    driver.quit()
    print("Client done.")

    httpd.shutdown()
    print("Server done.")


if __name__ == "__main__":
    main()
