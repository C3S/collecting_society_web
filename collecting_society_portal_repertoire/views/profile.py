# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from pyramid.view import (
    view_config,
    view_defaults
)

from collecting_society_portal.models import (
    Tdb,
    WebUser
)

from collecting_society_portal.views import ViewBase

from collecting_society_portal.resources import ProfileResource

from .forms import (
    EditProfile
)

log = logging.getLogger(__name__)


@view_defaults(context=ProfileResource)
class ProfileViews(ViewBase):

    @view_config(
        name='',
        permission='profile_root')
    def root(self):
        return self.redirect(ProfileResource, 'show')

    @view_config(
        name='show',
        renderer='../templates/profile/show.pt',
        permission='show_profile')
    def show(self):
        _webuser = WebUser.current_web_user(self.request)
        if _webuser is None:
            return None
        return {
            'webuser': _webuser,
            'member': True
        }

    @view_config(
        name='edit',
        renderer='../templates/profile/edit.pt',
        permission='edit_profile')
    def edit(self):
        self.register_form(EditProfile)
        return self.process_forms()
