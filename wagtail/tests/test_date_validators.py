import datetime
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from wagtail.fields import NoFutureDateValidator


class TestNoFutureDateValidator(TestCase):
    def setUp(self):
        self.validator = NoFutureDateValidator()

    def test_validates_past_date(self):
        """Past dates should pass validation"""
        past_date = datetime.date.today() - datetime.timedelta(days=1)
        # Should not raise ValidationError
        self.validator(past_date)

    def test_validates_today(self):
        """Today's date should pass validation"""
        today = datetime.date.today()
        # Should not raise ValidationError
        self.validator(today)

    def test_rejects_future_date(self):
        """Future dates should raise ValidationError"""
        future_date = datetime.date.today() + datetime.timedelta(days=1)
        with self.assertRaises(ValidationError) as cm:
            self.validator(future_date)

        self.assertEqual(cm.exception.code, "future_date")
        self.assertEqual(str(cm.exception.message), "Date cannot be in the future.")

    def test_validates_none_value(self):
        """None values should pass validation (let required validation handle empty values)"""
        # Should not raise ValidationError
        self.validator(None)

    def test_custom_message(self):
        """Test custom error message"""
        custom_message = "Custom future date error message"
        validator = NoFutureDateValidator(message=custom_message)
        future_date = datetime.date.today() + datetime.timedelta(days=1)

        with self.assertRaises(ValidationError) as cm:
            validator(future_date)

        self.assertEqual(str(cm.exception.message), custom_message)

    @patch("wagtail.fields.datetime")
    def test_validates_with_mocked_today(self, mock_datetime):
        """Test that validation uses the correct 'today' reference"""
        # Mock today to be 2024-01-15
        mock_today = datetime.date(2024, 1, 15)
        mock_datetime.date.today.return_value = mock_today

        # Test date exactly one day in the future
        future_date = datetime.date(2024, 1, 16)
        with self.assertRaises(ValidationError):
            self.validator(future_date)

        # Test date exactly 'today'
        self.validator(mock_today)  # Should not raise

        # Test past date
        past_date = datetime.date(2024, 1, 14)
        self.validator(past_date)  # Should not raise
