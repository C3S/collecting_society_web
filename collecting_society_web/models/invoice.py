# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class Invoice(Tdb):
    """
    Model wrapper for Tryton model object 'account.invoice'
    """
    __name__ = 'account.invoice'

    @classmethod
    def search(cls, domain, offset=None, limit=None, order=None,
               escape=False):
        """
        Searches invoices by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          obj: list of invoices
        """
        # prepare query
        if escape:
            domain = cls.escape_domain(domain)
        # search
        result = cls.get().search(domain, offset, limit, order)
        return result

    @classmethod
    def current_viewable(cls, request, type):
        """
        Searches invoices of type 'in', which the current web_user is allowed
        to view.

        Args:
          request (pyramid.request.Request): Current request.
          type (str): invoice type ('in' or 'out')

        Returns:
          list: viewable invoices of current web_user
          None: if no match is found
        """
        return cls.search_viewable(
            request.web_user, type=type, state=request.GET.get('state', ''))

    @classmethod
    def search_viewable(cls, web_user, type='', active=True, state=''):
        """
        Searches declarations, which the web_user is allowed to view.

        Args:
          web_user_id (int): web.user.id
          type (str): invoice type ('in' or 'out')
          state (str): declaration state filter

        Returns:
          list: viewable declarations of web_user, empty if none were found
        """
        # sanity checks
        if type not in ['in', 'out']:
            return None
        # default
        domain = [
            ('party', '=', web_user.party),
            ('type', '=', type),
        ]
        order = [('invoice_date', 'DESC')]
        # finished
        if state == 'finished':
            domain.append(('state', 'in', ['paid', 'cancelled']))
        # other
        else:
            domain.append(('state', '=', 'posted'))
        return cls.get().search(domain, order=order)

    @classmethod
    def search_by_number(cls, number):
        """
        Searches an invoice by invoice number

        Args:
          number (str): invoice.number

        Returns:
          obj: invoice
          None: if no match is found
        """
        result = cls.get().search([
            ('number', '=', number),
        ])
        if not result:
            return None
        return result[0]
