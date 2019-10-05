# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from pyramid.view import (
    view_config,
    view_defaults
)

from portal_web.views import ViewBase

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.RepertoireResource')
class RepertoireViews(ViewBase):

    @view_config(
        name='',
        permission='authenticated')
    def root(self):
        return self.redirect('dashboard')

    @view_config(
        name='dashboard',
        renderer='../templates/repertoire/dashboard.pt',
        permission='authenticated')
    def dashboard(self):
        return {}
