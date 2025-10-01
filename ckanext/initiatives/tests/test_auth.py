"""Tests for auth.py."""

import pytest

import ckan.tests.factories as factories
import ckan.tests.helpers as test_helpers
import ckan.model as model
import ckan.logic as logic
from ckan.common import g

@pytest.mark.ckan_config("ckan.plugins", "initiatives")
@pytest.mark.usefixtures("with_request_context", "with_plugins", "clean_db")
class TestInitiativesAuth(object):
    pass
