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

from ..resources import RepertoireResource

log = logging.getLogger(__name__)


@view_defaults(context=RepertoireResource)
class RepertoireViews(ViewBase):

    @view_config(
        name='',
        permission='read'
    )
    def root(self):
        return self.redirect(RepertoireResource, 'dashboard')

    @view_config(
        name='dashboard',
        renderer='../templates/repository/dashboard.pt',
        permission='read'
    )
    def dashboard(self):
        return {}

    @view_config(
        name='upload',
        renderer='../templates/repository/upload.pt',
        permission='read'
    )
    def upload(self):
        return {}
