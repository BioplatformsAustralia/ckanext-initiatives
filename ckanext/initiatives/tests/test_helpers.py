"""Tests for helpers.py."""

import pytest
import logging
import ckan.tests.factories as factories
import ckan.plugins
import ckan.plugins.toolkit as tk
import ckanext.initiatives.helpers as initiatives_helpers
import ckan.model as model
from ckan.common import g

log = logging.getLogger(__name__)


@pytest.mark.ckan_config("ckan.plugins", "initiatives")
@pytest.mark.usefixtures("with_plugins", "with_request_context")
class TestInitativesHelpers(object):
    def test_initiatives_get_user_id(self):
        user = factories.User()

        userobj = model.User.by_name(user["name"])

        g.user = user["name"]
        g.userobj = userobj

        assert initiatives_helpers.initiatives_get_user_id() == user["name"]
