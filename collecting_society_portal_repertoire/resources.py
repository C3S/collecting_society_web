# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

from collecting_society_portal.resources import (
    ResourceBase,
    BackendResource,
    DebugResource
)


class ArtistResource(ResourceBase):
    __name__ = "artists"
    __parent__ = None
    __children__ = {}
    __registry__ = {}
    __acl__ = []


class ReleaseResource(ResourceBase):
    __name__ = "releases"
    __parent__ = None
    __children__ = {}
    __registry__ = {}
    __acl__ = []


class CreationResource(ResourceBase):
    __name__ = "creations"
    __parent__ = None
    __children__ = {}
    __registry__ = {}
    __acl__ = []


class RepertoireResource(ResourceBase):
    __name__ = "repertoire"
    __parent__ = BackendResource
    __children__ = {}
    __registry__ = {}
    __acl__ = []


class UploadResource(ResourceBase):
    __name__ = "upload"
    __parent__ = RepertoireResource
    __children__ = {}
    __registry__ = {}
    __acl__ = []


class DebugC3sMembershipApiResource(ResourceBase):
    __name__ = "membership"
    __parent__ = DebugResource
    __children__ = {}
    __registry__ = {}
    __acl__ = []
