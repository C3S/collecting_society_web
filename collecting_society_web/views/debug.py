# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import uuid

from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import (
    view_config,
    view_defaults
)

from portal_web.views import ViewBase

from ..services import C3SMembershipApiClient

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.DebugC3sMembershipApiResource',
    permission=NO_PERMISSION_REQUIRED,
    environment='development')
class DebugC3sMembershipApiViews(ViewBase):

    def __init__(self, context, request):
        super(DebugC3sMembershipApiViews, self).__init__(context, request)
        settings = self.request.registry.settings
        self.membership = C3SMembershipApiClient(
            base_url=settings['api.c3smembership.url'],
            version=settings['api.c3smembership.version'],
            api_key=settings['api.c3smembership.api_key']
        )

    @view_config(
        name='echo',
        renderer='json')
    def echo(self):
        return self.membership.echo(
            message=str(uuid.uuid4())
        )

    @view_config(
        name='is_member',
        renderer='json')
    def is_member(self):
        return self.membership.is_member(
            service='repertoire',
            email='test@test.test'
        )

    @view_config(
        name='generate_member_token',
        renderer='json')
    def generate_member_token(self):
        return self.membership.generate_member_token(
            service='repertoire',
            email='test@test.test'
        )

    @view_config(
        name='search_member',
        renderer='json')
    def search_member(self):
        return self.membership.search_member(
            service='repertoire',
            email='test@test.test',
            token='MEMBER_TOKEN'
        )
