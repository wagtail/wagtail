from django.core.files.base import ContentFile


def get_test_document_file():
    fake_file = ContentFile(b"A boring example document")
    fake_file.name = "test.txt"
    return fake_file
