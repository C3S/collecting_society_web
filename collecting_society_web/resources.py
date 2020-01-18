# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import re

from pyramid.security import (
    Allow,
    DENY_ALL,
    NO_PERMISSION_REQUIRED,
)

from portal_web.resources import (
    ResourceBase,
    ModelResource,
    BackendResource,
    DebugResource
)

from .models import (
    Artist,
    Release,
    Creation,
    Content,
    Device
)

log = logging.getLogger(__name__)


# --- Regex -------------------------------------------------------------------

valid = {
    'artist': r'^A\d{10}\Z',
    'release': r'^R\d{10}\Z',
    'creation': r'^C\d{10}\Z',
    'content': r'^D\d{10}\Z',
    'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z'
}


# --- Repertoire Resources ----------------------------------------------------

class RepertoireResource(ResourceBase):
    __parent__ = BackendResource
    __name__ = "repertoire"
    __acl__ = [
        # add basic access for user with the role licenser
        (Allow, 'licenser', (
            'authenticated',
            'list_artists',
            'list_creations',
            'list_releases',
            'list_content',
            'add_artist',
            'add_creation',
            'add_release',
            'add_content',
        )),
        # prevent inheritance from backend resource
        DENY_ALL
    ]


class ArtistsResource(ResourceBase):
    """
    matches the webusers artists after clicking Artists in the Repertoire menu
    """
    __parent__ = RepertoireResource
    __name__ = "artists"
    _write = ['add']

    # traversal
    def __getitem__(self, key):
        # validate code
        if re.match(valid['artist'], key):
            return ArtistResource(self.request, key)
        # views needing writable transactions
        if key in self._write:
            self.readonly = False
        raise KeyError(key)

    # load resources
    def context_found(self):
        if self.request.view_name == '':
            self.artists = Artist.current_viewable(self.request)


class ArtistResource(ModelResource):
    """
    matches a single artist after clicking one in Repertoire -> Artists
    """
    __parent__ = ArtistsResource
    _write = ['edit', 'delete']
    _permit = ['view_artist', 'edit_artist', 'delete_artist']

    # load resources
    def context_found(self):
        self.artist = Artist.search_by_code(self.code)

    # add instance level permissions
    def __acl__(self):
        if not hasattr(self.artist, 'permissions'):
            return []
        return [
            (Allow, self.request.authenticated_userid,
                self.artist.permissions(self.request.web_user, self._permit))
        ]


class ReleasesResource(ResourceBase):
    """
    matches the webusers releases when clicking Releases in the Repertoire menu
    """
    __parent__ = RepertoireResource
    __name__ = "releases"
    _write = ['add']

    # traversal
    def __getitem__(self, key):
        # validate code
        if re.match(valid['release'], key):
            return ReleaseResource(self.request, key)
        # views needing writable transactions
        if key in self._write:
            self.readonly = False
        raise KeyError(key)

    # load resources
    def context_found(self):
        if self.request.view_name == '':
            self.releases = Release.current_viewable(self.request)


class ReleaseResource(ModelResource):
    """
    matches a single release after clicking one in Repertoire -> Release
    """
    __parent__ = ReleasesResource
    _write = ['edit', 'delete']
    _permit = ['view_release', 'edit_release', 'delete_release']

    # load resources
    def context_found(self):
        self.release = Release.search_by_code(self.code)

    # add instance level permissions
    def __acl__(self):
        if not hasattr(self.release, 'permissions'):
            return []
        return [
            (Allow, self.request.authenticated_userid,
                self.release.permissions(self.request.web_user, self._permit))
        ]


class CreationsResource(ResourceBase):
    """
    matches the webusers creations if clicking Creations in the Repertoire menu
    """
    __parent__ = RepertoireResource
    __name__ = "creations"
    _write = ['add']

    # traversal
    def __getitem__(self, key):
        # validate code
        if re.match(valid['creation'], key):
            return CreationResource(self.request, key)
        # views needing writable transactions
        if key in self._write:
            self.readonly = False
        raise KeyError(key)

    # load resources
    def context_found(self):
        if self.request.view_name == '':
            self.creations = Creation.current_viewable(self.request)
        # in add creation, provide content uuid, set by upload form
        if self.request.view_name == 'add':
            uuid = self.request.params.get('uuid', '')
            if re.match(valid['uuid'], uuid):
                self.content = Content.search_by_uuid(uuid)


class CreationResource(ModelResource):
    """
    matches a single creation after clicking one in Repertoire -> Creations
    """
    __parent__ = CreationsResource
    _write = ['edit', 'delete']
    _permit = ['view_creation', 'edit_creation', 'delete_creation']

    # load resources
    def context_found(self):
        self.creation = Creation.search_by_code(self.code)

    # add instance level permissions
    def __acl__(self):
        if not hasattr(self.creation, 'permissions'):
            return []
        return [
            (Allow, self.request.authenticated_userid,
                self.creation.permissions(self.request.web_user, self._permit))
        ]


class FilesResource(ResourceBase):
    """
    matches the webusers files after clicking Files in the Repertoire menu
    """
    __parent__ = RepertoireResource
    __name__ = "files"
    _write = ['add']

    # traversal
    def __getitem__(self, key):
        # validate code
        if re.match(valid['content'], key):
            return FileResource(self.request, key)
        # views needing writable transactions
        if key in self._write:
            self.readonly = False
        raise KeyError(key)

    # load resources
    def context_found(self):
        if self.request.view_name == '':
            self.files = Content.current_viewable(self.request)


class FileResource(ModelResource):
    """
    matches a single file after clicking one in Repertoire -> Files
    """
    __parent__ = FilesResource
    _write = ['delete']
    _permit = ['view_content', 'delete_content']

    # load resources
    def context_found(self):
        self.file = Content.search_by_code(self.code)

    # add instance level permissions
    def __acl__(self):
        if not hasattr(self.file, 'permissions'):
            return []
        return [
            (Allow, self.request.authenticated_userid,
                self.file.permissions(self.request.web_user, self._permit))
        ]


class DebugC3sMembershipApiResource(ResourceBase):
    __parent__ = DebugResource
    __name__ = "membership"


# --- Licensing Resources -----------------------------------------------------


class LicensingResource(ResourceBase):
    __parent__ = BackendResource
    __name__ = "licensing"
    __acl__ = [
        # add basic access for user with the role licensee
        (Allow, 'licensee', (
            'authenticated',
            'list_devices',
            'add_device',
        )),
        # prevent inheritance from backend resource
        DENY_ALL
    ]


class DevicesResource(ResourceBase):
    """
    matches the webusers devices after clicking Devices Files in Licensing menu
    """
    __parent__ = LicensingResource
    __name__ = "devices"
    _write = ['add']

    # traversal
    def __getitem__(self, key):
        # validate code
        if re.match(valid['uuid'], key):
            return DeviceResource(self.request, key)
        # views needing writable transactions
        if key in self._write:
            self.readonly = False
        raise KeyError(key)

    # load resources
    def context_found(self):
        if self.request.view_name == '':
            self.devices = Device.current_viewable(self.request)


class DeviceResource(ModelResource):
    """
    matches a single device after clicking one in Licensing -> Devices
    """
    __parent__ = DevicesResource
    _write = ['delete']
    _permit = ['view_device', 'delete_device']

    # load resources
    def context_found(self):
        self.device = Device.search_by_uuid(self.code)



    


