"""
Natural key implementations for Wagtail models to enable Django serialization framework.

This module adds natural_key() and get_by_natural_key() methods to Wagtail models
that don't have them, enabling proper serialization/deserialization.
"""

default_app_config = 'wagtail.contrib.natural_keys.apps.NaturalKeysConfig'
