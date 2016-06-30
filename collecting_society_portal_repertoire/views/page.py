# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from pyramid.renderers import render
from pyramid.response import (
    Response,
    FileResponse
)
from pyramid.security import (
    remember,
    NO_PERMISSION_REQUIRED
)
from pyramid.view import (
    view_config,
    view_defaults
)

from collecting_society_portal.resources import (
    FrontendResource,
    BackendResource
)
from collecting_society_portal.models import (
    Tdb,
    WebUser
)
from collecting_society_portal.views import ViewBase
from collecting_society_portal.views.forms import (
    LoginWebuser
)

from ..services import _
from .forms import RegisterWebuser

log = logging.getLogger(__name__)


@view_defaults(
    context=FrontendResource,
    permission=NO_PERMISSION_REQUIRED)
class PagePortalViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/page/home.pt')
    def home(self):
        self.register_form(LoginWebuser)
        self.register_form(RegisterWebuser)
        return self.process_forms()

    @view_config(
        name='verify_email',
        decorator=Tdb.transaction(readonly=False))
    def verify_email(self):

        # sanity checks
        opt_in_uuid = False
        if self.request.subpath:
            opt_in_uuid = self.request.subpath[-1]

        # change opt in state
        if opt_in_uuid:
            web_user = WebUser.search_by_opt_in_uuid(str(opt_in_uuid))
            if web_user:
                web_user.opt_in_state = 'opted-in'
                web_user.save()
                self.request.session.flash(
                    _(u"Your email verification was successful."),
                    'main-alert-success'
                )
                log.info("web_user login successful: %s" % web_user.email)
                return self.redirect(
                    BackendResource, '',
                    headers=remember(self.request, web_user.email)
                )
            else:
                self.request.session.flash(
                    _(
                        u"Your email verification was not successful "
                        u"(wrong validation code)."
                    ),
                    'main-alert-danger'
                )
        else:
            self.request.session.flash(
                _(
                    u"Your email verification was not successful "
                    u"(no validation code)."
                ),
                'main-alert-danger'
            )

        return self.redirect(FrontendResource)
