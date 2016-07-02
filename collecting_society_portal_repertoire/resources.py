# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

from collecting_society_portal.resources import (
    ResourceBase,
    BackendResource,
    DebugResource
)


class RepertoireResource(ResourceBase):
    __name__ = "repository"
    __parent__ = BackendResource
    __children__ = {}
    __registry__ = {}
    __acl__ = []


class DebugC3sMembershipApiResource(ResourceBase):
    __name__ = "membership"
    __parent__ = DebugResource
    __children__ = {}
    __registry__ = {}
    __acl__ = []
