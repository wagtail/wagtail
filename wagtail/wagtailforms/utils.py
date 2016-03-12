import os
import shutil

from django.utils.six import string_types
import antispam

# To be set if a custom model should be used (and trained)
ANTISPAM_MODEL_FILE = "my_model.dat"


def get_detector():
    # Return the default antispam detector with its builtin model or, if applicable, a detector with a custom model
    detector = antispam

    if ANTISPAM_MODEL_FILE:
        if not os.path.isfile(ANTISPAM_MODEL_FILE):
            copy_default_model()

        detector = antispam.Detector(ANTISPAM_MODEL_FILE)

    return detector


def get_msg_from_data(data):
    # Return all strings in given data dictionary as a concatenated message
    text_content = ""

    for value in data.itervalues():
        if isinstance(value, string_types):
            text_content += " " + value

    return text_content


def is_spam(data):
    # Check if data is presumably spam
    msg = get_msg_from_data(data)

    return get_detector().is_spam(msg) if msg else False


def train_spam_recognition(data, spam, priviledged=False):
    # Only train custom models
    if ANTISPAM_MODEL_FILE:
        msg = get_msg_from_data(data)
        detector = get_detector()
        score = detector.score(msg)

        # Only train detector when receiving priviledged requests or high/low quality messages
        if priviledged or score < 0.15 or score > 0.85:
            detector.train(msg, spam)
            detector.save()


def copy_default_model():
    # Workaround to get the default model path
    antispam.score("foo")
    shutil.copy(antispam.module.obj.model.DEFAULT_DATA_PATH, ANTISPAM_MODEL_FILE)
