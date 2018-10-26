# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from pyramid.view import (
    view_config,
    view_defaults
)

from collecting_society_portal.views import ViewBase
from collecting_society_portal.resources import ProfileResource

from .forms import (
    EditProfile
)

log = logging.getLogger(__name__)


@view_defaults(
    context=ProfileResource,
    permission='authenticated')
class ProfileViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/profile/show.pt')
    def show(self):
        return {}

    @view_config(
        name='edit',
        renderer='../templates/profile/edit.pt')
    def edit(self):
        self.register_form(EditProfile)
        return self.process_forms()
