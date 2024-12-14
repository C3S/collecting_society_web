# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb, MixinSearchById

log = logging.getLogger(__name__)


class Declaration(Tdb, MixinSearchById):
    """
    Model wrapper for Tryton model object 'declaration'
    """
    __name__ = 'declaration'

    @classmethod
    def current_viewable(cls, request):
        """
        Searches declarations, which the current web_user is allowed to view.

        Args:
          request (pyramid.request.Request): Current request.

        Returns:
          list: viewable declarations of current web_user
          None: if no match is found
        """
        return cls.search_viewable_by_web_user(
            request.web_user.id, state=request.GET.get('state', ''))

    @classmethod
    def search_viewable_by_web_user(cls, web_user_id, active=True, state=''):
        """
        Searches declarations, which the web_user is allowed to view.

        Args:
          web_user_id (int): web.user.id
          state (str): declaration state filter

        Returns:
          list: viewable declarations of web_user, empty if none were found
        """
        domain = [('licensee.web_user', '=', web_user_id)]
        order = []
        # finished
        if state == 'finished':
            domain.append(('state', '=', 'finished'))
        # other
        else:
            domain.append(('state', '=', 'submitted'))
            order.append(('period', 'ASC'))
        order.append(('code', 'ASC'))
        return cls.get().search(domain, order=order)

    @classmethod
    def search_by_code(cls, declaration_code, active=True):
        """
        Searches a declaration by declaration code

        Args:
          declaration_code (int): declaration.code

        Returns:
          obj: declaration
          None: if no match is found
        """
        result = cls.get().search([
            ('code', '=', declaration_code),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]
