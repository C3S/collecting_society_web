# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from ...services import _
from ...models import Invoice

from portal_web.helpers import format_currency


class UnpaidInvoicesWidget():

    def __init__(self, request):
        self.unpaid_invoices = [{
                'number': invoice.number,
                'date': invoice.invoice_date,
                'amount': format_currency(invoice.amount_to_pay),
            } for invoice in Invoice.search([
                ('party', '=', request.party),
                ('type', '=', 'out'),
                ('state', '=', 'posted'),
            ], order=[('invoice_date', 'DESC')])
        ]

    def condition(self):
        return bool(self.unpaid_invoices)

    def icon(self):
        return "element-icon-invoices-yellow.svg"

    def badge(self):
        return len(self.unpaid_invoices)

    def header(self):
        return _("Unpaid Invoices")

    def description(self):
        return _("Please pay your Invoices:")

    def links(self):
        return [{
            'name': f"#{invoice['number']} | "
                    f"{invoice['date']} | "
                    f"{invoice['amount']} ",
            'path': ['licensing', 'invoices', invoice['number']],
        } for invoice in self.unpaid_invoices]

    def buttons(self):
        return False
