# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from pyramid.response import Response
from pyramid.view import (
    view_config,
    view_defaults
)

from portal_web.views import ViewBase

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.RoyaltiesResource')
class RoyaltiesViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/royalty/list.pt',
        permission='list_royalties')
    def list(self):
        return {}


@view_defaults(
    context='..resources.RoyaltyResource')
class RoyaltyViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/royalty/show.pt',
        permission='view_royalty')
    def show(self):
        return {}

    @view_config(
        name='download',
        permission='download_royalty')
    def download(self):
        royalty = self.context.royalty
        response = Response(
            content_type=f'application/{royalty.invoice_report_format}')
        response.body = royalty.invoice_report_cache
        company_name = royalty.company.party.name.replace(" ", "_").lower()
        extension = royalty.invoice_report_format
        filename = f"{company_name}-royalty-{royalty.number}.{extension}"
        response.content_disposition = f'attachment; filename="{filename}"'
        return response
