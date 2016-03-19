import os
import shutil

from django.utils.six import string_types
import antispam


class BaseSpamDetector(object):
    @staticmethod
    def is_spam(message):
        # Check if data is presumably spam, always returns False
        return False

    @staticmethod
    def score(message):
        # Score the possibility that data is spam, always returns 0
        return 0

    @staticmethod
    def train(message, is_spam, priviledged=False):
        # Train the detector, nothing to do here
        pass


class AntiSpamDetector(BaseSpamDetector):
    def __init__(self, *args, **kwargs):
        # Return the default antispam detector with its builtin model or, if applicable, a detector with a custom model
        self.detector = antispam
        # TODO: should be configured in settings instead of being hardcoded
        self.model = "my_model.dat"

        if self.model:
            if not os.path.isfile(self.model):
                self.copy_default_model()

            self.detector = antispam.Detector(self.model)

    def copy_default_model(self):
        # Workaround to get the default model path
        self.detector.score("foo")
        shutil.copy(antispam.module.obj.model.DEFAULT_DATA_PATH, self.model)

    def is_spam(self, message):
        # Check if data is presumably spam
        return self.detector.is_spam(message) if message else False

    def score(self, message):
        # Score the possibility that data is spam
        return self.detector.score(message)

    def train(self, message, is_spam, priviledged=False):
        # Train the detector, only when using custom models
        if self.model:
            score = self.score(message)

            # Only train detector when receiving priviledged requests or high/low quality messages
            if priviledged or score < 0.15 or score > 0.85:
                self.detector.train(message, is_spam)
                self.detector.save()


def get_message_from_dict(data):
    # Return all strings in given data dictionary as a concatenated message
    text_content = ""

    for value in data.itervalues():
        if isinstance(value, string_types):
            text_content += " " + value

    return text_content
