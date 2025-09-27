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
    context='..resources.InvoicesResource')
class InvoicesViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/invoice/list.pt',
        permission='list_invoices')
    def list(self):
        return {}


@view_defaults(
    context='..resources.InvoiceResource')
class InvoiceViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/invoice/show.pt',
        permission='view_invoice')
    def show(self):
        return {}

    @view_config(
        name='download',
        permission='download_invoice')
    def download(self):
        invoice = self.context.invoice
        response = Response(
            content_type=f'application/{invoice.invoice_report_format}')
        response.body = invoice.invoice_report_cache
        company_name = invoice.company.party.name.replace(" ", "_").lower()
        extension = invoice.invoice_report_format
        filename = f"{company_name}-invoice-{invoice.number}.{extension}"
        response.content_disposition = f'attachment; filename="{filename}"'
        return response
