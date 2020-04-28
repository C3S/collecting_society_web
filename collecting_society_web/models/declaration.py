# For copyright and genre terms, see COPYRIGHT.rst (top level of repository)
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
    def belongs_to_current_licensee(cls, request):
        """
        returns all objects that belong to a certain licensee

        Args:
          request (pyramid.request.Request): Current request.

        Returns:
          list: objects that belong to the licensee
          None: if no match is found
        """
        return cls.get().search([('licensee', '=',
                                request.web_user.party.id)])
