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
class TestIniativesHelpers(object):
    pass
