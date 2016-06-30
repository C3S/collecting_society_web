# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import (
    view_config,
    view_defaults
)

from collecting_society_portal.views import ViewBase

from ..services import C3SMembershipApiClient

log = logging.getLogger(__name__)


@view_defaults(
    context='collecting_society_portal.resources.DebugResource',
    permission=NO_PERMISSION_REQUIRED,
    environment='development')
class DebugViews(ViewBase):

    @view_config(
        name='test',
        renderer='json')
    def test(self):
        membership = C3SMembershipApiClient(
            'http://c3sadorepertoire_api_1/c3smembership/v1',
            'api_key'
        )
        return membership.echo('test')
