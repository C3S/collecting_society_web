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
from collecting_society_portal.models import (
    Tdb,
    WebUser
)

from ..services import _

log = logging.getLogger(__name__)


@view_defaults(
    context=BackendResource,
    permission='authenticated')
class BackendViews(ViewBase):

    @view_config(
        name='')
    def dashboard(self):
        return self.redirect('repertoire')

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

        # sanity checks
        opt_in_uuid = False
        if self.request.subpath:
            opt_in_uuid = self.request.subpath[-1]

        # new email activation
        web_user = WebUser.search_by_opt_in_uuid(str(opt_in_uuid))
        if web_user:
            if web_user.new_email:
                web_user.email = web_user.new_email
                web_user.new_email = ''
                web_user.save()
            self.request.session.flash(
                _(u"Your email verification was successful. "
                    u"Now login with your new email address!"),
                'main-alert-success'
            )
            log.info("email activation successful: %s" % web_user.email)
            return self.redirect(
                FrontendResource
            )

        else:
            self.request.session.flash(
                _(
                    u"Your email verification was not successful "
                    u"(no validation code)."
                ),
                'main-alert-danger'
            )

        return self.redirect()
