# coding: utf8

from __future__ import unicode_literals
from six import string_types, text_type
from inspect import currentframe, getframeinfo
import ckan.authz as authz
from ckan.common import _
from ckan.common import config

import ckan.lib.mailer as mailer
import ckan.logic as logic
import ckan.plugins.toolkit as toolkit
import datetime
import functools

from logging import getLogger

log = getLogger(__name__)


class UserOrganizations:
    def __init__(self, user):
        self.org_names = set()
        self.org_ids = set()

        context = {"user": user}
        data_dict = {"permission": "read"}

        for org in logic.get_action("organization_list_for_user")(context, data_dict):
            org_name = org.get("name")
            if org_name is not None:
                self.org_names.add(org_name)
            org_id = org.get("id")
            if org_id is not None:
                self.org_ids.add(org_id)
                # If the org has a parent, add the parent to the list of orgs.
                # This allows users that are members of organizations with a parent of a consortium level org
                # to access embargoed data.
                # Implemented to facilitate AAI implementation of groups that are separate from exsiting CKAN access
                org_show_dict = {"id": org_id}
                # Do not query for the group datasets when dictizing, as they will
                # be ignored and get requested on the controller anyway
                org_show_dict["include_datasets"] = False
                org_show_dict["include_users"] = False
                org_show_dict["include_extras"] = True
                org_with_extras = logic.get_action("organization_show")(context, org_show_dict)
                if (org_with_extras):
                    print(str(org_with_extras))
                    for group in org_with_extras["groups"]:
                         parent_name = group.get("name")
                         if parent_name is not None:
                             self.org_names.add(parent_name)

def get_key_maybe_extras(obj, name):
    # scheming may have put the field on 'extras'
    if isinstance(obj.get("extras"), list):
        extras = {str(k): text_type(v) for k, v in obj.get("extras", [])}
    else:
        extras = obj.get("extras", {})
    return obj.get(name, extras.get(name, ""))


def initiatives_get_username_from_context(context):
    auth_user_obj = context.get("auth_user_obj", None)
    user_name = ""
    if auth_user_obj:
        user_name = auth_user_obj.as_dict().get("name", "")
    else:
        if authz.get_user_id_for_username(context.get("user"), allow_none=True):
            user_name = context.get("user", "")
    return user_name


def access_granted(organization=None):
    retval = {"success": True}

    if organization:
        retval["result"] = organization

    return retval


def access_denied(organization=None):
    # log calling location to assist debugging
    cf = currentframe()
    log.info(
        "access denied %d %s" % (cf.f_back.f_lineno, getframeinfo(cf.f_back).filename)
    )

    retval = {
        "success": False,
        "msg": "Resource access restricted to registered users",
    }

    if organization:
        retval["result"] = organization
    else:
        retval["error"] = {
            "__type": "Access Permissions Error",
            "message": "Unable to determine permissions for access",
        }

    return retval


def check_extra_args(nargs):
    def decorator_check_args(fn):
        @functools.wraps(fn)
        def check(u, r, p, *args):
            if len(args) != nargs:
                return access_denied(None)
            return fn(u, r, p, *args)

        return check

    return decorator_check_args


@check_extra_args(0)
def apply_organization_member(user, resource_dict, package_dict):
    # must be logged in as a registered user
    if not user:
        return access_denied(None)

    pkg_organization_id = package_dict.get("owner_org", "")

    # check if the user is a full consortium member
    user_orgs = UserOrganizations(user)

    if pkg_organization_id in user_orgs.org_ids:
        return access_granted(pkg_organization_id)
    return access_denied(pkg_organization_id)


@check_extra_args(3)
def apply_access_after(
    user, resource_dict, package_dict, field_name, days, consortium_org_name
):
    """
    access to resources if the user is:
      - a member of owner_org; and
      - the date (YYYY-MM-DD) in `field_name` is more than `days` days ago
    OR
      - the user is a member of `consortium_org_name` (which can be used to track
      users who are members of the consortium
    """

    # must be logged in as a registered user
    if not user:
        return access_denied(None)

    # check if the user is a full consortium member
    user_orgs = UserOrganizations(user)
    if consortium_org_name and consortium_org_name in user_orgs.org_names:
        return access_granted(consortium_org_name)

    # check if the data is out of embargo
    try:
        days = int(days)
    except ValueError:
        days = None
    dt_str = get_key_maybe_extras(package_dict, field_name)
    try:
        dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d").date()
    except (ValueError, TypeError) as e:
        dt = None

    # we can't work out the dates: deny access
    if days is None or dt is None:
        return access_denied(None)

    today = datetime.date.today()
    d_days = (today - dt).days
    if d_days >= days:
        # out of embargo: grant access if the user is a member of the owner_org
        return apply_organization_member(user, resource_dict, package_dict)
    else:
        # data in embargo: deny access
        return access_denied(consortium_org_name)


@check_extra_args(0)
def apply_public(user, resource_dict, package_dict):
    return access_granted()


PERMISSION_HANDLERS = {
    "organization_member_after_embargo": apply_access_after,
    "organization_member": apply_organization_member,
    "public": apply_public,
}


def parse_resource_permissions(permission_str):
    """
    syntax is:
    handler_name:arg1:arg2
    """
    parts = [t.strip() for t in permission_str.split(":")]

    name = ""
    args = []

    if len(parts) > 0:
        name, args = parts[0], parts[1:]

    # a safe, restrictive default: we never seek to restrict
    # data beyond organization members
    if name not in PERMISSION_HANDLERS:
        name = "organization_member"

    return lambda u, r, p: PERMISSION_HANDLERS[name](u, r, p, *args)


def initiatives_check_user_resource_access(user, resource_dict, package_dict):
    """
    note: calling methods will check if the user has write-access to the enclosing
    package (they are an admin or manager), in which case this method will not be
    called
    """

    resource_permissions = get_key_maybe_extras(package_dict, "resource_permissions")
    permission_handler = parse_resource_permissions(resource_permissions)

    return permission_handler(user, resource_dict, package_dict)
