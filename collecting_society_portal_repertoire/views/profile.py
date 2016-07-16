# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from pyramid.view import (
    view_config,
    view_defaults
)

from collecting_society_portal.views import ViewBase
from collecting_society_portal.resources import ProfileResource

from ..services import C3SMembershipApiClient

log = logging.getLogger(__name__)


@view_defaults(context=ProfileResource)
class ProfileViews(ViewBase):

    @view_config(
        name='',
        permission='read'
    )
    def dashboard(self):
        return self.redirect(ProfileResource, 'show')

    @view_config(
        name='show',
        renderer='../templates/profile/show.pt',
        permission='read'
    )
    def show(self):
        return {
            'member': True
        }

    @view_config(
        name='edit',
        renderer='../templates/profile/edit.pt',
        permission='read'
    )
    def edit(self):
        return {}
