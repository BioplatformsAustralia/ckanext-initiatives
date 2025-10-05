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
    def test_initiatives_resource_show_with_user(self):
        user = factories.User()
        # simulate logged in session
        userobj = model.User.by_name(user["name"])
        g.user = user["name"]
        g.userobj = userobj

        owner_org = factories.Organization(
            users=[{"name": user["id"], "capacity": "member"}]
        )
        package = factories.Dataset(owner_org=owner_org["id"])
        resource = factories.Resource(package_id=package["id"])
        context = {"user": user["name"], "model": model, "resource": resource}

        data_dict = {"id": resource["id"]}

        assert test_helpers.call_auth("resource_show", context=context, data_dict=data_dict)
