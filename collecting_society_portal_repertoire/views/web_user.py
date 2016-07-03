# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from pyramid.security import forget
from pyramid.httpexceptions import HTTPFound
from pyramid.view import (
    view_config,
    view_defaults
)

from collecting_society_portal.views import ViewBase
from collecting_society_portal.resources import (
    FrontendResource,
    BackendResource
)

from ..resources import RepertoireResource

log = logging.getLogger(__name__)


@view_defaults(context=BackendResource)
class WebUserViews(ViewBase):

    @view_config(
        name='',
        permission='read'
    )
    def dashboard(self):
        return self.redirect(RepertoireResource)

    @view_config(
        name='logout',
        permission='read'
    )
    def logout(self):
        self.request.session.invalidate()
        log.info(
            "web_user logout successful: %s" %
            self.request.unauthenticated_userid
        )
        headers = forget(self.request)
        return HTTPFound(
            self.request.resource_path(FrontendResource(self.request)),
            headers=headers
        )
