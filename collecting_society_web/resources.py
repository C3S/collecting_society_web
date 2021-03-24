# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import re

from pyramid.security import (
    Allow,
    DENY_ALL,
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
    Declaration,
    Location,
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
            'list_declarations',
            'add_declaration',
            'list_locations',
            'add_location',
        )),
        # prevent inheritance from backend resource
        DENY_ALL
    ]


class DeclarationsResource(ResourceBase):
    """
    matches the webusers declarations after clicking Declarations in the
    Licensing menu
    """
    __parent__ = LicensingResource
    __name__ = "declarations"
    _write = ['add']

    # traversal
    def __getitem__(self, key):
        # validate code
        if re.match(valid['uuid'], key):
            return DeclarationResource(self.request, key)
        # views needing writable transactions
        if key in self._write:
            self.readonly = False
        raise KeyError(key)

    # load resources
    def context_found(self):
        if self.request.view_name == '':
            self.declarations = Declaration.belongs_to_current_licensee(
                                self.request)


class DeclarationResource(ModelResource):
    """
    matches a single declaration after clicking in Licensing -> Declarations
    """
    __parent__ = DeclarationsResource
    _write = ['edit', 'delete']

    # load resources
    def context_found(self):
        self.declaration = Declaration.search_by_uuid(self.code)

    # add instance level permissions
    def __acl__(self):
        declaration_in_database = Declaration.search_by_uuid(self.code)
        if (declaration_in_database and
                self.declaration.web_user == declaration_in_database.web_user):
            return [
                (Allow, self.request.authenticated_userid,
                    ['show_declaration', 'edit_declaration',
                     'delete_declaration'])
            ]
        return []


class LocationsResource(ResourceBase):
    """
    matches the locations the webusers is allowed to see or change
    """
    __parent__ = LicensingResource
    __name__ = "locations"
    _write = ['add']

    # traversal
    def __getitem__(self, key):
        # validate oid
        if re.match(valid['uuid'], key):
            return LocationResource(self.request, key)
        # views needing writable transactions
        if key in self._write:
            self.readonly = False
        raise KeyError(key)

    # load resources
    def context_found(self):
        if self.request.view_name == '':
            self.locations = Location.search_by_entity_creator(
                self.request.web_user.party.id)


class LocationResource(ModelResource):
    """
    matches a single location after clicking one in Licensing -> Location
    """
    __parent__ = LocationsResource
    _write = ['edit', 'delete']

    # load resources
    def context_found(self):
        self.location = Location.search_by_oid(self.code)

    # only allow write access, if this webuser created the location
    def __acl__(self):
        location_in_db = Location.search_by_oid(self.code)
        if (location_in_db and
                self.request.web_user.party == location_in_db.entity_creator):
            return [
                (Allow, self.request.authenticated_userid,
                    ['show_location', 'edit_location', 'delete_location'])
            ]
        return []


class DevicesResource(ResourceBase):
    """
    matches the webusers locations after clicking Devices Files in Licensing
    menu
    """
    __parent__ = LicensingResource
    __name__ = "devices"
    _write = ['add']

    # traversal
    def __getitem__(self, key):
        # validate uuid
        if re.match(valid['uuid'], key):
            return DeviceResource(self.request, key)
        # views needing writable transactions
        if key in self._write:
            self.readonly = False
        raise KeyError(key)

    # load resources
    def context_found(self):
        if self.request.view_name == '':
            self.devices = Device.belongs_to_current_webuser(self.request)
        # in add creation, provide content uuid, set by upload form
        if self.request.view_name == 'add':
            device_id = self.request.params.get('device_id', '')
            if re.match(valid['uuid'], device_id):
                self.device_id = device_id
            device_name = self.request.params.get('device_name', '')
            if len(device_name) > 0:
                self.device_name = device_name
            os_name = self.request.params.get('os_name', '')
            if len(os_name) > 0:
                self.os_name = os_name
            os_version = self.request.params.get('os_version', '')
            if len(os_version) > 0:
                self.os_version = os_version
            software_name = self.request.params.get('software_name', '')
            if len(software_name) > 0:
                self.software_name = software_name
            software_version = self.request.params.get('software_version', '')
            if len(software_version) > 0:
                self.software_version = software_version
            software_vendor = self.request.params.get('software_vendor', '')
            if len(software_vendor) > 0:
                self.software_vendor = software_vendor


class DeviceResource(ModelResource):
    """
    matches a single device after clicking one in Licensing -> Devices
    """
    __parent__ = DevicesResource
    _write = ['edit', 'delete']

    # load resources
    def context_found(self):
        self.device = Device.search_by_uuid(self.code)

    # add instance level permissions
    def __acl__(self):
        device_in_database = Device.search_by_uuid(self.code)
        if (device_in_database and
                self.device.web_user == device_in_database.web_user):
            return [
                (Allow, self.request.authenticated_userid,
                    ['show_device', 'edit_device', 'delete_device'])
            ]
        return []


class AccountingResource(ResourceBase):
    """
    matches the webusers accounting infos after clicking Accounting in
    Licensing menu
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
        # in add creation, provide content uuid, set by upload form
        if self.request.view_name == 'add':
            device_id = self.request.params.get('device_id', '')
            if re.match(valid['uuid'], device_id):
                self.device_id = device_id
            device_name = self.request.params.get('device_name', '')
            if len(device_name) > 0:
                self.device_name = device_name
            os_name = self.request.params.get('os_name', '')
            if len(os_name) > 0:
                self.os_name = os_name
            os_version = self.request.params.get('os_version', '')
            if len(os_version) > 0:
                self.os_version = os_version
            software_name = self.request.params.get('software_name', '')
            if len(software_name) > 0:
                self.software_name = software_name
            software_version = self.request.params.get('software_version', '')
            if len(software_version) > 0:
                self.software_version = software_version
            software_vendor = self.request.params.get('software_vendor', '')
            if len(software_vendor) > 0:
                self.software_vendor = software_vendor


class AccountingItemResource(ModelResource):
    """
    matches a single item after clicking one in Licensing -> Accounting
    """
    __parent__ = AccountingResource
    _write = ['edit', 'delete']

    # load resources
    def context_found(self):
        self.device = Device.search_by_uuid(self.code)

    # add instance level permissions
    def __acl__(self):
        device_in_database = Device.search_by_uuid(self.code)
        if (device_in_database and
                self.device.web_user == device_in_database.web_user):
            return [
                (Allow, self.request.authenticated_userid,
                    ['show_device', 'edit_device', 'delete_device'])
            ]
        return []


class StatisticsResource(ResourceBase):
    """
    matches the webusers statistics after clicking Statistics in Licensing menu
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
        # in add creation, provide content uuid, set by upload form
        if self.request.view_name == 'add':
            device_id = self.request.params.get('device_id', '')
            if re.match(valid['uuid'], device_id):
                self.device_id = device_id
            device_name = self.request.params.get('device_name', '')
            if len(device_name) > 0:
                self.device_name = device_name
            os_name = self.request.params.get('os_name', '')
            if len(os_name) > 0:
                self.os_name = os_name
            os_version = self.request.params.get('os_version', '')
            if len(os_version) > 0:
                self.os_version = os_version
            software_name = self.request.params.get('software_name', '')
            if len(software_name) > 0:
                self.software_name = software_name
            software_version = self.request.params.get('software_version', '')
            if len(software_version) > 0:
                self.software_version = software_version
            software_vendor = self.request.params.get('software_vendor', '')
            if len(software_vendor) > 0:
                self.software_vendor = software_vendor


class StatisticsItemResource(ModelResource):
    """
    matches a single item after clicking one in Licensing -> Statistics
    """
    __parent__ = StatisticsResource
    _write = ['edit', 'delete']

    # load resources
    def context_found(self):
        self.device = Device.search_by_uuid(self.code)

    # add instance level permissions
    def __acl__(self):
        device_in_database = Device.search_by_uuid(self.code)
        if (device_in_database and
                self.device.web_user == device_in_database.web_user):
            return [
                (Allow, self.request.authenticated_userid,
                    ['show_device', 'edit_device', 'delete_device'])
            ]
        return []
