# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import uuid

from pyramid.security import (
    remember,
    NO_PERMISSION_REQUIRED
)
from pyramid.view import (
    view_config,
    view_defaults
)

from portal_web.resources import (
    FrontendResource,
    BackendResource
)
from portal_web.models import (
    Tdb,
    WebUser
)
from portal_web.views import ViewBase
from portal_web.views.forms import LoginWebuser

from ..services import _
from .forms import RegisterWebuser

log = logging.getLogger(__name__)


@view_defaults(
    context=FrontendResource,
    permission=NO_PERMISSION_REQUIRED)
class FrontentViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/frontend/home.pt')
    @view_config(
        name='register',
        renderer='../templates/frontend/home.pt')
    def home(self):
        self.register_form(LoginWebuser)
        self.register_form(RegisterWebuser)
        return self.process_forms()

    @view_config(
        name='verify_email',
        decorator=Tdb.transaction(readonly=False))
    def verify_email(self):
        return verify_email_helper(self)


def verify_email_helper(the_class):
    """
    also used by backend.py
    """

    # sanity checks
    opt_in_uuid = False
    if the_class.request.subpath:
        opt_in_uuid = the_class.request.subpath[-1]

    # change opt in state
    if opt_in_uuid:
        web_user = WebUser.search_by_opt_in_uuid(str(opt_in_uuid))
        if web_user:
            if web_user.opt_in_state != 'opted-in':
                web_user.opt_in_state = 'opted-in'
            else:  # already opted in? then this is a new email activation
                if web_user.new_email:
                    web_user.email = web_user.new_email
                    web_user.new_email = ''
            # invalidate uuid
            web_user.opt_in_uuid = str(uuid.uuid4())  # noqa: F821
            web_user.save()
            the_class.request.session.flash(
                _(u"Your email verification was successful."),
                'main-alert-success'
            )
            log.info("web_user login successful: %s" % web_user.email)
            return the_class.redirect(
                BackendResource, '',
                headers=remember(the_class.request, web_user.email)
            )
        else:
            the_class.request.session.flash(
                _(
                    u"Your email verification was not successful "
                    u"(wrong validation code)."
                ),
                'main-alert-danger'
            )
    else:
        the_class.request.session.flash(
            _(
                u"Your email verification was not successful "
                u"(no validation code)."
            ),
            'main-alert-danger'
        )

    return the_class.redirect()
