"""
Tests for action.py.
"""
import pytest

import ckan.model as model
import ckan.logic
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
import ckan.plugins.toolkit as tk
import ckanext.initiatives.plugins as plugins

@pytest.mark.ckan_config("ckan.plugins", "initiatives image_view")
@pytest.mark.usefixtures("with_plugins")
class TestInitiativesAction(object):
    @pytest.mark.usefixtures("clean_db")
    def test_resource_view_list_no_resource(self):
        user = factories.User()
        resource_id = "nonexistent"

        context = {'ignore_auth': True, 'user': user['name']}

        result = helpers.call_action('resource_view_list', context, id=resource_id)

        assert result == []

    @pytest.mark.usefixtures("clean_db")
    def test_resource_view_list_authorized(self):
        user = factories.User()
        owner_org = factories.Organization(users=[{ 'name': user['id'],
            'capacity': 'admin'
        }])
        package = factories.Dataset(owner_org=owner_org['id'])
        resource = factories.Resource(
            package_id=package['id'],
            url="http://some.image.png",
            format="png",
            name="Image 1",
            )

        resource_id = resource['id']

        context = {'ignore_auth': False, 'user': user['name']}

        result = helpers.call_action('resource_view_list', context, id=resource_id)

        assert len(result) == 1
        assert result[0]["view_type"] == "image_view"

    @pytest.mark.usefixtures("clean_db")
    def test_resource_view_list_unauthorized(self):
        user = factories.User()
        user2 = factories.User()
        owner_org = factories.Organization(users=[{
            'name': user['id'],
            'capacity': 'admin'
        }])
        package = factories.Dataset(owner_org=owner_org['id'])
        resource = factories.Resource(
            package_id=package['id'],
            url="http://some.image.png",
            format="png",
            name="Image 1",
            )

        resource_id = resource['id']

        context = {'ignore_auth': False, 'user': user2['name']}

        result = helpers.call_action('resource_view_list', context, id=resource_id)

        assert result == []

    @pytest.mark.usefixtures("clean_db")
    def test_initiatives_check_access_no_package_id(self):
        user = factories.User()
        owner_org = factories.Organization(users=[{ 'name': user['id'],
            'capacity': 'admin'
        }])
        package = factories.Dataset(owner_org=owner_org['id'])
        resource = factories.Resource(
            package_id=package['id'],
            url="http://some.image.png",
            format="png",
            name="Image 1",
            )

        resource_id = resource['id']

        context = {'ignore_auth': True, 'user': user['name']}

        with pytest.raises(ckan.logic.ValidationError, match='Missing package_id') as e:
            result = helpers.call_action('initiatives_check_access', context, package_id=None, resource_id=resource_id)

        assert e.type is ckan.logic.ValidationError

    @pytest.mark.usefixtures("clean_db")
    def test_initiatives_check_access_no_resource_id(self):
        user = factories.User()
        owner_org = factories.Organization(users=[{ 'name': user['id'],
            'capacity': 'admin'
        }])
        package = factories.Dataset(owner_org=owner_org['id'])
        resource = factories.Resource(
            package_id=package['id'],
            url="http://some.image.png",
            format="png",
            name="Image 1",
            )

        package_id = package['id']

        context = {'ignore_auth': True, 'user': user['name']}

        with pytest.raises(ckan.logic.ValidationError, match='Missing resource_id') as e:
            result = helpers.call_action('initiatives_check_access', context, package_id=package_id, resource_id=None)

        assert e.type is ckan.logic.ValidationError

    @pytest.mark.usefixtures("clean_db")
    def test_initiatives_check_access_permitted(self):
        user = factories.User()
        owner_org = factories.Organization(users=[{ 'name': user['id'],
            'capacity': 'admin'
        }])
        package = factories.Dataset(owner_org=owner_org['id'])
        resource = factories.Resource(
            package_id=package['id'],
            url="http://some.image.png",
            format="png",
            name="Image 1",
            )

        package_id = package['id']
        resource_id = resource['id']

        context = {'ignore_auth': False, 'user': user['name']}

        result = helpers.call_action('initiatives_check_access', context, package_id=package_id, resource_id=resource_id)

        assert result.get("success") is True

    @pytest.mark.usefixtures("clean_db")
    def test_initiatives_check_access_denied(self):
        user = factories.User()
        user2 = factories.User()
        owner_org = factories.Organization(users=[{ 'name': user['id'],
            'capacity': 'admin'
        }])
        package = factories.Dataset(owner_org=owner_org['id'])
        resource = factories.Resource(
            package_id=package['id'],
            url="http://some.image.png",
            format="png",
            name="Image 1",
            )

        package_id = package['id']
        resource_id = resource['id']

        context = {'ignore_auth': False, 'user': user2['name']}

        result = helpers.call_action('initiatives_check_access', context, package_id=package_id, resource_id=resource_id)

        assert result.get("success") is False
