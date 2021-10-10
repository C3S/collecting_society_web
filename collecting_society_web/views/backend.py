# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from pyramid.security import forget
from pyramid.httpexceptions import HTTPFound
from pyramid.view import (
    view_config,
    view_defaults
)

from portal_web.views import ViewBase
from portal_web.resources import (
    FrontendResource,
    BackendResource
)
from portal_web.models import Tdb

from .frontend import verify_email_helper

log = logging.getLogger(__name__)


@view_defaults(
    context=BackendResource,
    permission='authenticated')
class BackendViews(ViewBase):

    @view_config(
        name='')
    def dashboard(self):
        return self.redirect('licensing')

    @view_config(
        name='help',
        renderer='../templates/backend/help.pt')
    def help(self):
        return {}

    @view_config(
        name='contact',
        renderer='../templates/backend/contact.pt')
    def contact(self):
        return {}

    @view_config(
        name='terms',
        renderer='../templates/backend/terms.pt')
    def terms(self):
        return {}

    @view_config(
        name='logout')
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

    @view_config(
        name='verify_email',
        decorator=Tdb.transaction(readonly=False))
    def verify_email(self):
        return verify_email_helper(self)
