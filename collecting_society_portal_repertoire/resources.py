# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging
import re

from pyramid.security import (
    Allow,
    Deny,
    DENY_ALL,
    Authenticated,
)
from pyramid.httpexceptions import (
    HTTPBadRequest
)

from collecting_society_portal.resources import (
    ResourceBase,
    BackendResource,
    ProfileResource,
    DebugResource
)
from collecting_society_portal.models import (
    Tdb,
    WebUser
)

from .models import Artist

log = logging.getLogger(__name__)


# --- Regex -------------------------------------------------------------------

re_artist = '^A\d{10}$'
re_release = '^R\d{10}$'
re_creation = '^C\d{10}$'
re_content = '^M\d{10}$'

# --- Resources ---------------------------------------------------------------

BackendResource.__acl__ = [
    (
        Allow, Authenticated, (
            'backend_root',
            'show_dashboard',
            'show_help',
            'show_contact',
            'show_terms',
            'logout',
            'verify_email',
        )),
    DENY_ALL
]


ProfileResource.__acl__ = [
    (
        Allow, Authenticated, (
            'profile_root',
            'show_profile',
            'edit_profile',
        )),
    DENY_ALL
]


class RepertoireResource(ResourceBase):
    __name__ = "repertoire"
    __acl__ = [
        (
            Allow, 'licenser', (
                'repertoire_root',
                'show_dashboard',
            )),
        DENY_ALL
    ]


class ArtistResource(ResourceBase):
    __name__ = "artists"
    __acl__ = [
        (
            Allow, 'licenser', (
                'artist_root',
                'list_aritsts',
                'show_artist',
                'add_artist',
                'edit_artist',
                'delete_artist'
            )),
        DENY_ALL
    ]


class EditArtistResource(ResourceBase):
    __name__ = "edit"
    __acl__ = []

    @Tdb.transaction(readonly=False)
    def __getitem__(self, key):
        # validate object code
        if not re.match(re_artist, key):
            return None
        # prepare resources
        self.artist = Artist.search_by_code(key)
        # add acls
        return self


class UploadResource(ResourceBase):
    __name__ = "upload"
    __acl__ = [
        (
            Allow, 'licenser', (
                'upload_files',
            )),
        DENY_ALL
    ]


class CreationResource(ResourceBase):
    __name__ = "creations"
    __acl__ = [
        (
            Allow, 'licenser', (
                'creation_root',
                'list_creations',
                'show_creation',
                'add_creation',
                'edit_creation',
                'delete_creation',
            )),
        DENY_ALL
    ]


class ReleaseResource(ResourceBase):
    __name__ = "releases"
    __acl__ = [
        (
            Allow, 'licenser', (
                'release_root',
                'list_releases',
                'show_release',
                'add_release',
                'edit_release',
                'delete_release',
            )),
        DENY_ALL
    ]


class DebugC3sMembershipApiResource(ResourceBase):
    __name__ = "membership"
    __parent__ = DebugResource
    __children__ = {}
    __registry__ = {}
    __acl__ = []
