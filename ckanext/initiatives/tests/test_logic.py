"""
Tests for logic.py.
"""
import pytest

import ckan.model as model
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
import ckan.plugins.toolkit as tk

from freezegun import freeze_time


import ckanext.initiatives.logic as initiatives_logic


@pytest.mark.ckan_config("ckan.plugins", "initiatives")
@pytest.mark.usefixtures("with_plugins")
class TestInitiativesLogic(object):
    @pytest.mark.usefixtures("clean_db")
    def test_initiatives_get_username_from_context_auth_user_obj(self):
        user = factories.User()
        # simulate logged in session
        userobj = model.User.by_name(user["name"])

        context = {
            "auth_user_obj": userobj,
        }
        result = initiatives_logic.initiatives_get_username_from_context(context)

        assert result == user["name"]

    @pytest.mark.usefixtures("clean_db")
    def test_check_extra_args(self):
        user = factories.User()
        owner_org = factories.Organization(
            users=[{"name": user["id"], "capacity": "member"}]
        )
        package = factories.Dataset(owner_org=owner_org["id"])
        resource = factories.Resource(package_id=package["id"])

        result = initiatives_logic.apply_organization_member(
            user["name"], resource, package, "unexpected extra arg"
        )

        assert result.get("success") == False

    @pytest.mark.usefixtures("clean_db")
    def test_apply_organization_member_success(self):
        user = factories.User()
        owner_org = factories.Organization(
            users=[{"name": user["id"], "capacity": "member"}]
        )
        package = factories.Dataset(owner_org=owner_org["id"])
        resource = factories.Resource(package_id=package["id"])

        result = initiatives_logic.apply_organization_member(
            user["name"], resource, package
        )

        assert result.get("success") == True

    @pytest.mark.usefixtures("clean_db")
    def test_apply_organization_member_nouser(self):
        user = factories.User()
        owner_org = factories.Organization(
            users=[{"name": user["id"], "capacity": "member"}]
        )
        package = factories.Dataset(owner_org=owner_org["id"])
        resource = factories.Resource(package_id=package["id"])

        result = initiatives_logic.apply_organization_member(None, resource, package)

        assert result.get("success") == False

    @pytest.mark.usefixtures("clean_db")
    def test_apply_organization_member_denied(self):
        user = factories.User()
        owner_org = factories.Organization(
            users=[{"name": user["id"], "capacity": "member"}]
        )
        package = factories.Dataset(owner_org=owner_org["id"])
        resource = factories.Resource(package_id=package["id"])

        user2 = factories.User()

        result = initiatives_logic.apply_organization_member(
            user2["name"], resource, package
        )

        assert result.get("success") == False

    @pytest.mark.usefixtures("clean_db")
    def test_apply_access_after_nouser(self):
        user = factories.User()
        owner_org = factories.Organization(
            users=[{"name": user["id"], "capacity": "member"}]
        )
        consortium_org = factories.Organization(
            parent=owner_org["name"],
            users=[
                {
                    "name": user["id"],
                    "capacity": "member",
                }
            ],
        )
        package = factories.Dataset(owner_org=owner_org["id"])
        resource = factories.Resource(package_id=package["id"])
        field_name = "date_of_transfer_to_archive"
        days = 7
        consortium_org_name = consortium_org["name"]

        result = initiatives_logic.apply_access_after(
            None, resource, package, field_name, days, consortium_org_name
        )

        assert result.get("success") == False

    @pytest.mark.usefixtures("clean_db")
    def test_apply_access_after_consortium_member(self):
        user = factories.User()
        user2 = factories.User()
        owner_org = factories.Organization(
            users=[{"name": user["id"], "capacity": "member"}]
        )
        consortium_org = factories.Organization(
            parent=owner_org["name"],
            users=[
                {
                    "name": user2["id"],
                    "capacity": "member",
                }
            ],
        )
        package = factories.Dataset(owner_org=owner_org["id"])
        resource = factories.Resource(package_id=package["id"])
        field_name = "date_of_transfer_to_archive"
        days = 7
        consortium_org_name = consortium_org["name"]

        result = initiatives_logic.apply_access_after(
            user2["name"], resource, package, field_name, days, consortium_org_name
        )

        assert result.get("success") == True

    @pytest.mark.usefixtures("clean_db")
    def test_apply_access_after_embargo(self):
        user = factories.User()
        user2 = factories.User()
        owner_org = factories.Organization(
            users=[{"name": user["id"], "capacity": "member"}]
        )
        consortium_org = factories.Organization(
            parent=owner_org["name"],
            users=[
                {
                    "name": user2["id"],
                    "capacity": "member",
                }
            ],
        )
        package = factories.Dataset(
            owner_org=owner_org["name"],
        )
        resource = factories.Resource(package_id=package["id"])
        field_name = "date_of_transfer_to_archive"
        package[field_name] = "2025-09-30"
        consortium_org_name = consortium_org["name"]
        days = 7

        # within embargo

        with freeze_time("2025-10-03 23:30:00"):
            result = initiatives_logic.apply_access_after(
                user["name"], resource, package, field_name, days, consortium_org_name
            )

        assert result.get("success") == False
        assert result.get("result") == consortium_org_name

        # outside embargo

        with freeze_time("2025-10-10 23:30:00"):
            result = initiatives_logic.apply_access_after(
                user["name"], resource, package, field_name, days, consortium_org_name
            )

        assert result.get("success") == True
        assert result.get("result") == owner_org["id"]

    @pytest.mark.usefixtures("clean_db")
    def test_apply_access_after_embargo_fields(self):
        user = factories.User()
        user2 = factories.User()
        owner_org = factories.Organization(
            users=[{"name": user["id"], "capacity": "member"}]
        )
        consortium_org = factories.Organization(
            parent=owner_org["name"],
            users=[
                {
                    "name": user2["id"],
                    "capacity": "member",
                }
            ],
        )
        package = factories.Dataset(
            owner_org=owner_org["name"],
        )
        resource = factories.Resource(package_id=package["id"])
        field_name = "date_of_transfer_to_archive"
        package[field_name] = "2025-09-30"
        consortium_org_name = consortium_org["name"]

        # days field string not formatted correctly
        days = "two"

        with freeze_time("2025-10-03 23:30:00"):
            result = initiatives_logic.apply_access_after(
                user["name"], resource, package, field_name, days, consortium_org_name
            )

        assert result.get("success") == False

        # bad date
        package[field_name] = "09-30-2025"
        days = 7

        with freeze_time("2025-10-10 23:30:00"):
            result = initiatives_logic.apply_access_after(
                user["name"], resource, package, field_name, days, consortium_org_name
            )

        assert result.get("success") == False

    @pytest.mark.usefixtures("clean_db")
    def test_apply_public(self):
        user = factories.User()
        owner_org = factories.Organization(
            users=[{"name": user["id"], "capacity": "admin"}]
        )
        package = factories.Dataset(owner_org=owner_org["id"])
        resource = factories.Resource(package_id=package["id"])

        result = initiatives_logic.apply_public(user["name"], resource, package)

        assert result.get("success") == True

    @pytest.mark.usefixtures("clean_db")
    def test_parse_resource_permissions_no_handler(self):
        user = factories.User()
        owner_org = factories.Organization(
            users=[{"name": user["id"], "capacity": "member"}]
        )
        package = factories.Dataset(
            owner_org=owner_org["id"],
            resource_permissions="",
        )
        resource = factories.Resource(package_id=package["id"])

        result = initiatives_logic.initiatives_check_user_resource_access(
            user["name"], resource, package
        )

        assert result.get("success") == True
