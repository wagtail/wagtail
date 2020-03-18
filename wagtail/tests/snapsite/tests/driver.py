from selenium.webdriver.chrome.webdriver import WebDriver, RemoteWebDriver


class DriverWithShortcuts(WebDriver):
    """Add shortcuts for common tasks to the Driver"""

    def click_link(self, link_text):
        self.find_element_by_link_text(link_text).click()

    def click_button(self, button_text):
        self.find_element_by_xpath(f"//button[text()='{button_text}']").click()

    def input_text(self, field_name, text):
        self.find_element_by_name(field_name).send_keys(text)

    def update_input_text(self, field_name, text):
        self.find_element_by_name(field_name).clear()
        self.find_element_by_name(field_name).send_keys(text)

    def scroll_to_bottom(self):
        self.execute_script("window.scrollTo(0, document.body.scrollHeight);")
