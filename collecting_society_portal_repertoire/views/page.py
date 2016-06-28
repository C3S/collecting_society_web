# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from pyramid.renderers import render
from pyramid.response import (
    Response,
    FileResponse
)
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import (
    view_config,
    view_defaults
)

from collecting_society_portal.resources import (
    FrontendResource,
    BackendResource
)
from collecting_society_portal.models import WebUser
from collecting_society_portal.views import ViewBase
from collecting_society_portal.views.forms import (
    LoginWebuser
)

from ..services import _
#from .forms import RegisterWebuser
from collecting_society_portal.views.forms import RegisterWebuser

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
        name='verify_email')
    def verify_email(self):

        # sanity checks
        opt_in_uuid = False
        if self.request.subpath:
            opt_in_uuid = self.request.subpath[-1]

        # change opt in state
        if opt_in_uuid:
            if WebUser.search_by_opt_in_uuid(str(opt_in_uuid)):
                if WebUser.update_opt_in_state(str(opt_in_uuid), 'opted-in'):
                    _type = 'main-alert-success'
                    _msg = _(u"Your email verification was successful.")
                else:
                    _type = 'main-alert-danger'
                    _msg = _(
                        u"Your email verification was not successful "
                        u"(update failed)."
                    )
            else:
                _type = 'main-alert-danger'
                _msg = _(
                    u"Your email verification was not successful "
                    u"(wrong validation code)."
                )
        else:
            _type = 'main-alert-danger'
            _msg = _(
                u"Your email verification was not successful "
                u"(no validation code)."
            )

        # user feedback
        self.request.session.flash(_msg, _type)

        return self.redirect(FrontendResource)
