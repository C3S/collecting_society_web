# coding=utf-8

# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

"""
Functions to include resources/views and register content by the plugin system.

The following functions are called by convention on app creation:

- web_resources
- web_registry
- web_views
- api_views
"""

from collections import OrderedDict

from collecting_society_portal.views.widgets import news_widget
from collecting_society_portal.resources import (
    FrontendResource,
    BackendResource,
    NewsResource,
    DebugResource
)

from collecting_society_portal_creative.resources import (
    ArtistResource,
    AddArtistResource,
    CreationResource
)

from .services import (
    _,
    C3SMembershipApiClient
)
from .resources import (
    RepertoireResource,
    DebugC3sMembershipApiResource
)
# from .views.widgets import (
#     ...
# )


def web_resources(config):
    '''
    Extends the resource tree for the web service.

    Note:
        The function is called by the plugin system, when the app is created.

    Args:
        config (pyramid.config.Configurator): App config

    Returns:
        None
    '''
    BackendResource.add_child(RepertoireResource)
    DebugResource.add_child(DebugC3sMembershipApiResource)


def web_registry(config):
    '''
    Extends the registry for content elements for the web service.

    Note:
        The function is called by the plugin system, when the app is created.

    Args:
        config (pyramid.config.Configurator): App config

    Returns:
        None
    '''
    settings = config.get_settings()

    @FrontendResource.extend_registry
    def frontend(self):
        reg = self.dict()
        # meta
        reg['meta'] = {
            'title': _(u'C3S - Repertoire'),
            'keywords': _(u'c3s,repertoire'),
            'description': _(u'registration of repertoire for C3S'),
            'languages': [
                # {
                #     'id': 'en',
                #     'name': _(u'english'),
                #     'icon': self.request.static_path(
                #         'collecting_society_portal:static/img/en.png'
                #     )
                # },
                # {
                #     'id': 'de',
                #     'name': _(u'deutsch'),
                #     'icon': self.request.static_path(
                #         'collecting_society_portal:static/img/de.png'
                #     )
                # }
            ]
        }
        # css
        reg['static']['css'] = [
            self.request.static_path(
                'collecting_society_portal_repertoire:static/css/frontend.css'
            )
        ]
        # favicon
        reg['static']['favicon'] = self.request.static_path(
            'collecting_society_portal_repertoire:static/img/favicon.png'
        )
        # logo
        reg['static']['logo'] = self.request.static_path(
            'collecting_society_portal_repertoire:static/img/logo-c3s.png'
        )
        # services
        reg['services']['c3smembership'] = C3SMembershipApiClient(
            base_url=settings['api.c3smembership.url'],
            version=settings['api.c3smembership.version'],
            api_key=settings['api.c3smembership.api_key']
        )
        # top menue
        reg['menues']['top'] = []
        if reg['services']['c3smembership'].is_connected():
            reg['menues']['top'] += [
                {
                    'name': _(u'register'),
                    'page': 'register'
                }
            ]
        reg['menues']['top'] += [
            {
                'name': _(u'about'),
                'page': 'about'
            },
            {
                'name': _(u'howto'),
                'page': 'howto'
            },
            {
                'name': _(u'contact'),
                'page': 'contact'
            },
            {
                'name': _(u'terms'),
                'page': 'terms'
            }
        ]
        return reg

    @BackendResource.extend_registry
    def backend(self):
        reg = self.dict()
        # css
        reg['static']['css'] = [
            self.request.static_path(
                'collecting_society_portal_repertoire:static/css/backend.css'
            )
        ]
        # logo
        reg['static']['logo'] = self.request.static_path(
            'collecting_society_portal_repertoire:static/img/logo-adore.png'
        )
        # main menue
        reg['menues']['roles'] = [
            {
                'name': _(u'Repertoire'),
                'active': RepertoireResource,
                'url': self.request.resource_path(
                    RepertoireResource(self.request), ''
                )
            }
        ]
        # top menue
        reg['menues']['top'] = [
            # {
            #     'name': _(u'News'),
            #     'url': self.request.resource_path(
            #         BackendResource(self.request), 'news'
            #     )
            # },
            # {
            #     'name': _(u'Contact'),
            #     'url': self.request.resource_path(
            #         BackendResource(self.request), 'contact'
            #     )
            # },
            # {
            #     'name': _(u'Imprint'),
            #     'url': self.request.resource_path(
            #         BackendResource(self.request), 'imprint'
            #     )
            # },
            # {
            #     'name': _(u'Logout'),
            #     'url': self.request.resource_path(
            #         BackendResource(self.request), 'logout'
            #     )
            # }
        ]
        # widgets content-right
        reg['widgets']['content-right'] = [
            # news_widget
        ]
        return reg


def web_views(config):
    '''
    Adds the views for the web service.

    Note:
        The function is called by the plugin system, when the app is created.

    Args:
        config (pyramid.config.Configurator): App config

    Returns:
        None
    '''
    config.add_static_view('static/repertoire', 'static', cache_max_age=3600)
    config.scan(ignore='.views.api')


def api_views(config):
    '''
    Adds the views for the api service.

    Note:
        The function is called by the plugin system, when the app is created.

    Args:
        config (pyramid.config.Configurator): App config

    Returns:
        None
    '''

    # routes
    # ...

    # views
    config.add_static_view(
        'static/repertoire', 'static', cache_max_age=3600,
        environment='development'
    )
    config.scan('.views.api')
