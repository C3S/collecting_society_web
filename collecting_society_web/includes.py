# coding=utf-8

# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

"""
Functions to include resources/views and register content by the plugin system.

The following functions are called by convention on app creation:

- web_resources
- web_registry
- web_views
- api_views
"""

import logging

from portal_web.resources import (
    FrontendResource,
    BackendResource,
    ProfileResource,
    DebugResource
)

from .services import _
from .resources import (
    ArtistsResource,
    ReleasesResource,
    CreationsResource,
    RepertoireResource,
    LicensingResource,
    FilesResource,
    DebugC3sMembershipApiResource,
    DeclarationsResource,
    LocationsResource,
    DevicesResource,
)
from .views.widgets import (
    ServiceInfoWidget,
    MissingArtistsWidget,
    MissingContentWidget,
    MissingReleasesWidget,
    RejectedContentWidget,
    OrphanedContentWidget,
    UnprocessedContentWidget
)

log = logging.getLogger(__name__)


def web_resources(config):
    """
    Extends the resource tree for the web service.

    Note:
        The function is called by the plugin system, when the app is created.

    Args:
        config (pyramid.config.Configurator): App config

    Returns:
        None
    """
    BackendResource.add_child(ProfileResource)
    BackendResource.add_child(RepertoireResource)
    BackendResource.add_child(LicensingResource)

    RepertoireResource.add_child(FilesResource)
    RepertoireResource.add_child(ArtistsResource)
    RepertoireResource.add_child(ReleasesResource)
    RepertoireResource.add_child(CreationsResource)

    LicensingResource.add_child(DeclarationsResource)
    LicensingResource.add_child(LocationsResource)
    LicensingResource.add_child(DevicesResource)
    LicensingResource.add_child(DeclarationsResource)

    DebugResource.add_child(DebugC3sMembershipApiResource)


def web_registry(config):
    """
    Extends the registry for content elements for the web service.

    Note:
        The function is called by the plugin system, when the app is created.

    Args:
        config (pyramid.config.Configurator): App config

    Returns:
        None
    """
    # Metadata shared by Frontend and Backend
    def meta(request):
        return {
            'title': _('C3S - Portal'),
            'keywords': _('c3s,portal,repertoire,licensing'),
            'description':
                _('registration of repertoire and utilisations for C3S'),
            'languages': [
                {
                    'id': 'en',
                    'name': _('english'),
                    'icon': request.static_path(
                                'portal_web:'
                                'static/img/en.png')},
                {
                    'id': 'de',
                    'name': _('deutsch'),
                    'icon': request.static_path(
                                'portal_web:'
                                'static/img/de.png')},
                # {
                #     'id': 'es',
                #     'name': _(u'español'),
                #     'icon': request.static_path(
                #                 'portal_web:'
                #                 'static/img/es.gif')}
            ]
        }

    @FrontendResource.extend_registry
    def frontend(self):
        reg = self.dict()
        # meta
        reg['meta'] = meta(self.request)
        # css
        reg['static']['css'] = [
            self.request.static_path(
                'collecting_society_web:'
                'static/css/frontend.css')
        ]
        # favicon
        reg['static']['favicon'] = self.request.static_path(
            'collecting_society_web:static/img/favicon.png')
        # logo
        reg['static']['logo'] = self.request.static_path(
            'collecting_society_web:static/img/logo-c3s.png')
        # top menue
        reg['menues']['top'] = [
            {
                'name': _('register'),
                'page': 'register'},
            {
                'name': _('test'),
                'page': 'test'},
            {
                'name': _('develop'),
                'page': 'develop'},
            {
                'name': _('terms'),
                'page': 'terms'}
        ]
        # widgets
        reg['widgets']['content-left'] = [
            ServiceInfoWidget(self.request),
        ]
        return reg

    @BackendResource.extend_registry
    def backend(self):
        reg = self.dict()
        # meta
        reg['meta'] = meta(self.request)
        # css
        reg['static']['css'] = [
            self.request.static_path(
                'portal_web:'
                'static/lib/DataTables/datatables.min.css'),
            self.request.static_path(
                'collecting_society_web:'
                'static/css/backend.css'),
        ]
        # js head
        reg['static']['js']['head'] = [
            {
                'src':  self.request.static_path(
                            'portal_web:'
                            'static/lib/JavaScript-Templates/js/tmpl.min.js')},
            {
                'src':  self.request.static_path(
                            'portal_web:'
                            'static/lib/DataTables/datatables.min.js')},
            {
                'src':  self.request.static_path(
                            'portal_web:'
                            'static/js/deform.datatables.widget.js')},
        ]
        # favicon
        reg['static']['favicon'] = self.request.static_path(
            'collecting_society_web:static/img/favicon.png')
        # logo
        reg['static']['logo'] = self.request.static_path(
            'collecting_society_web:static/img/logo-c3s.png')
        # top menue
        reg['menues']['top'] = [
            {
                'name': _('Profile'),
                'url':  self.request.resource_path(
                            BackendResource(self.request), 'profile')},
            {
                'name': _('Help'),
                'url':  self.request.resource_path(
                            BackendResource(self.request), 'help')},
            {
                'name': _('Contact'),
                'url':  self.request.resource_path(
                            BackendResource(self.request), 'contact')},
            {
                'name': _('Terms'),
                'url':  self.request.resource_path(
                            BackendResource(self.request), 'terms')},
            {
                'name': _('Logout'),
                'url':  self.request.resource_path(
                            BackendResource(self.request), 'logout')}
        ]
        # main menue
        reg['menues']['roles'] = [
            {
                'name': _('Repertoire'), 'active': RepertoireResource,
                'url':  self.request.resource_path(
                            RepertoireResource(self.request), '')},
            {
                'name': _('Licensing'), 'active': LicensingResource,
                'url':  self.request.resource_path(
                            LicensingResource(self.request), '')}
        ]
        return reg

    @RepertoireResource.extend_registry
    def repertoire(self):
        reg = self.dict()
        # css
        reg['static']['css'] = [
            self.request.static_path(
                'portal_web:'
                'static/lib/DataTables/datatables.min.css'),
            self.request.static_path(
                'collecting_society_web:'
                'static/css/backend.css'),
            self.request.static_path(
                'collecting_society_web:'
                'static/css/backend-repertoire.css'),
        ]
        # main repertoire menue
        reg['menues']['main'] = [
            {
                'name': _('Dashboard'),
                'url':  self.request.resource_path(
                            RepertoireResource(self.request), 'dashboard'),
                'icon': self.request.static_path(
                            'collecting_society_web:'
                            'static/img/element-icon-dashboard.png')},
            {
                'name': _('Files'),
                'url':  self.request.resource_path(
                            FilesResource(self.request)),
                'icon': self.request.static_path(
                            'collecting_society_web:'
                            'static/img/element-icon-upload.png')},
            {
                'name': _('Artists'),
                'url':  self.request.resource_path(
                            ArtistsResource(self.request)),
                'icon': self.request.static_path(
                            'collecting_society_web:'
                            'static/img/element-icon-soloartists.png')},
            {
                'name': _('Creations'),
                'url':  self.request.resource_path(
                            CreationsResource(self.request)),
                'icon': self.request.static_path(
                            'collecting_society_web:'
                            'static/img/element-icon-songs.png')},
            {
                'name': _('Releases'),
                'url':  self.request.resource_path(
                            ReleasesResource(self.request)),
                'icon': self.request.static_path(
                            'collecting_society_web:'
                            'static/img/element-icon-releases.png')},
        ]
        # widgets
        reg['widgets']['dashboard-central-widgets'] = [
            MissingArtistsWidget(self.request),
            MissingContentWidget(self.request),
            MissingReleasesWidget(self.request),
            RejectedContentWidget(self.request),
            OrphanedContentWidget(self.request),
            # UncommitedContentWidget(self.request),
            UnprocessedContentWidget(self.request),
        ]
        return reg

    @LicensingResource.extend_registry
    def licensing(self):
        reg = self.dict()
        # css
        reg['static']['css'] = [
            self.request.static_path(
                'portal_web:'
                'static/lib/DataTables/datatables.min.css'),
            self.request.static_path(
                'collecting_society_web:'
                'static/css/backend.css'),
            self.request.static_path(
                'collecting_society_web:'
                'static/css/backend-licensing.css'),
        ]
        # role menue
        reg['menues']['roles'] = [
            {
                'name': _('Repertoire'), 'active': RepertoireResource,
                'url':  self.request.resource_path(
                            RepertoireResource(self.request), '')},
            {
                'name': _('Licensing'), 'active': LicensingResource,
                'url':  self.request.resource_path(
                            LicensingResource(self.request), '')}
        ]
        # main licensing menue
        reg['menues']['main'] = [
            {
                'name': _('Dashboard'),
                'url':  self.request.resource_path(
                            LicensingResource(self.request), 'dashboard'),
                'icon': self.request.static_path(
                            'collecting_society_web:static/img/'
                            'element-icon-dashboard.png')},
            {
                'name': _('Declarations'),
                'url':  self.request.resource_path(
                            DeclarationsResource(self.request)),
                'icon': self.request.static_path(
                            'collecting_society_web:static/img/'
                            'element-icon-declarations.svg')},
            {
                'name': _('Locations'),
                'url':  self.request.resource_path(
                            LocationsResource(self.request)),
                'icon': self.request.static_path(
                            'collecting_society_web:static/img/'
                            'element-icon-locations.svg')},
            {
                'name': _('Devices'),
                'url':  self.request.resource_path(
                            DevicesResource(self.request)),
                'icon': self.request.static_path(
                            'collecting_society_web:static/img/'
                            'element-icon-devices.svg')},
            # {
            #     'name': _(u'Accounting'),
            #     'url':  self.request.resource_path(
            #                 DevicesResource(self.request)),
            #     'icon': self.request.static_path(
            #                 'collecting_society_web:static/img/'
            #                 'element-icon-accounting.svg')},
            # {
            #     'name': _(u'Statistics'),
            #     'url':  self.request.resource_path(
            #                 DevicesResource(self.request)),
            #     'icon': self.request.static_path(
            #                 'collecting_society_web:static/img/'
            #                 'element-icon-statistics.svg')},
        ]
        # widgets
        # ToDo
        return reg

    @FilesResource.extend_registry
    def upload(self):
        reg = self.dict()
        jfu = 'portal_web:static/lib/jQuery-File-Upload/'
        # css
        reg['static']['css'] = [
            self.request.static_path(
                'collecting_society_web:'
                'static/css/backend.css'),
            self.request.static_path(
                'collecting_society_web:'
                'static/css/backend-repertoire.css'),
            self.request.static_path(
                jfu + 'css/jquery.fileupload.css'),
            self.request.static_path(
                jfu + 'css/jquery.fileupload-ui.css')
        ]
        # js
        reg['static']['js']['body'] = [
            {
                "src": self.request.static_path(
                    jfu + 'js/vendor/jquery.ui.widget.js')},
            {
                "src": self.request.static_path(
                    'portal_web:'
                    'static/lib/JavaScript-Load-Image/js/'
                    'load-image.all.min.js')},
            {
                "src": self.request.static_path(
                    jfu + 'js/jquery.iframe-transport.js')},
            {
                "src": self.request.static_path(
                    jfu + 'js/jquery.fileupload.js')},
            {
                "src": self.request.static_path(
                    jfu + 'js/jquery.fileupload-process.js')},
            {
                "src": self.request.static_path(
                    jfu + 'js/jquery.fileupload-audio.js')},
            {
                "src": self.request.static_path(
                    jfu + 'js/jquery.fileupload-validate.js')},
            {
                "src": self.request.static_path(
                    jfu + 'js/jquery.fileupload-ui.js')},
            {
                "src": self.request.static_path(
                    'collecting_society_web:'
                    'static/js/jquery.fileupload.init.js')},
            {
                "src": self.request.static_path(
                    'portal_web:static/js/portal.js')},
        ]
        return reg


def web_views(config):
    """
    Adds the views for the web service.

    Note:
        The function is called by the plugin system, when the app is created.

    Args:
        config (pyramid.config.Configurator): App config

    Returns:
        None
    """
    config.add_static_view(
        'static/collecting_society', 'static', cache_max_age=3600)
    config.scan(ignore=['.views.api', '.tests'])


def api_views(config):
    """
    Adds the views for the api service.

    Note:
        The function is called by the plugin system, when the app is created.

    Args:
        config (pyramid.config.Configurator): App config

    Returns:
        None
    """
    config.add_static_view(
        'static/collecting_society', 'static', cache_max_age=3600,
        environment='testing')
    config.scan('.views.api')
