from django.test import SimpleTestCase

from wagtail.test.utils.form_data import querydict_from_html


class TestQueryDictFromHTML(SimpleTestCase):
    html = """
    <form id="personal-details">
        <input type="hidden" name="csrfmiddlewaretoken" value="Z783HTL5Bc2J54WhAtEeR3eefM1FBkq0EbTfNnYnepFGuJSOfvosFvwjeKYtMwFr">
        <input type="hidden" name="no_value_input">
        <input type="hidden" value="no name input">
        <div>
            <div>
                <label>
                    <span>Full name</span>
                    <input type="text" name="name" value="Jane Doe" placeholder="">
                </label>
                <label>
                    <span>Email address</span>
                    <input type="email" name="email" value="jane@example.com" placeholder="name@example.com">
                </label>
            </div>
        </div>
    </form>
    <form id="event-details">
        <div>
            <div>
                <label>
                    <span>When is your event?</span>
                    <input type="date" name="date" value="2023-01-01">
                </label>
                <label>
                    <span>What type of event is it?</span>
                    <select name="event_type">
                        <option value="corporate">Corporate event</option>
                        <option value="wedding">Wedding</option>
                        <option value="birthday">Birthday</option>
                        <option value="other" selected>Other</option>
                    </select>
                </label>
                <label>
                    <span>What age groups is it suitable for?</span>
                    <select name="ages" multiple>
                        <option>Infants</option>
                        <option>Children</option>
                        <option>Teenagers</option>
                        <option selected>18-30</option>
                        <option selected>30-50</option>
                        <option>50-70</option>
                        <option>70+</option>
                    </select>
                </label>
            </div>
        </div>
    </form>
    <form id="market-research">
        <div>
            <div>
                <fieldset>
                    <legend>How many pets do you have?</legend>
                    <div class="radio-list">
                        <div class="radio">
                            <label>
                                <input type="radio" name="pets" value="0" />
                                None
                            </label>
                        </div>
                        <div class="radio">
                            <label>
                                <input type="radio" name="pets" value="1" />
                                One
                            </label>
                        </div>
                        <div class="radio">
                            <label>
                                <input type="radio" name="pets" value="2" checked />
                                Two
                            </label>
                        </div>
                        <div class="radio">
                            <label>
                                <input type="radio" name="pets" value="3+" />
                                Three or more
                            </label>
                        </div>
                    </div>
                </fieldset>
                <fieldset>
                    <legend>Which two colours do you like best?</legend>
                    <div class="checkbox-list">
                        <div class="checkbox">
                            <label>
                                <input type="checkbox" name="colours" value="cyan">
                                Cyan
                            </label>
                        </div>
                        <div class="checkbox">
                            <label>
                                <input type="checkbox" name="colours" value="magenta" checked />
                                Magenta
                            </label>
                        </div>
                        <div class="checkbox">
                            <label>
                                <input type="checkbox" name="colours" value="yellow" />
                                Yellow
                            </label>
                        </div>
                        <div class="checkbox">
                            <label>
                                <input type="checkbox" name="colours" value="black" checked />
                                Black
                            </label>
                        </div>
                        <div class="checkbox">
                            <label>
                                <input type="checkbox" name="colours" value="white" />
                                White
                            </label>
                        </div>
                    </div>
                </fieldset>
                <label>
                    <span>Tell us what you love</span>
                    <textarea name="love" rows="3">Comic books</textarea>
                </label>
            </div>
        </div>
    </form>
    """

    personal_details = [
        ("no_value_input", [""]),
        ("name", ["Jane Doe"]),
        ("email", ["jane@example.com"]),
    ]

    event_details = [
        ("date", ["2023-01-01"]),
        ("event_type", ["other"]),
        ("ages", ["18-30", "30-50"]),
    ]

    market_research = [
        ("pets", ["2"]),
        ("colours", ["magenta", "black"]),
        ("love", ["Comic books"]),
    ]

    def test_html_only(self):
        # data should be extracted from the 'first' form by default
        result = querydict_from_html(self.html)
        self.assertEqual(list(result.lists()), self.personal_details)

    def test_include_csrf(self):
        result = querydict_from_html(self.html, exclude_csrf=False)
        expected_result = [
            (
                "csrfmiddlewaretoken",
                ["Z783HTL5Bc2J54WhAtEeR3eefM1FBkq0EbTfNnYnepFGuJSOfvosFvwjeKYtMwFr"],
            )
        ] + self.personal_details
        self.assertEqual(list(result.lists()), expected_result)

    def test_form_index(self):
        for index, expected_data in (
            (0, self.personal_details),
            ("2", self.market_research),
            (1, self.event_details),
        ):
            result = querydict_from_html(self.html, form_index=index)
            self.assertEqual(list(result.lists()), expected_data)

    def test_form_id(self):
        for id, expected_data in (
            ("event-details", self.event_details),
            ("personal-details", self.personal_details),
            ("market-research", self.market_research),
        ):
            result = querydict_from_html(self.html, form_id=id)
            self.assertEqual(list(result.lists()), expected_data)

    def test_invalid_form_id(self):
        with self.assertRaises(ValueError):
            querydict_from_html(self.html, form_id="invalid-id")

    def test_invalid_index(self):
        with self.assertRaises(ValueError):
            querydict_from_html(self.html, form_index=5)
