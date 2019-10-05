# For copyright and style terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class Style(Tdb):
    """
    Model wrapper for Tryton model object 'style'
    """

    __name__ = 'style'

    @classmethod
    def search_all(cls):
        """
        Fetches all Styles

        Returns:
          list: styles
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    def search_by_name(cls, name):
        """
        Searches a style by name

        Args:
          name (string): style.name

        Returns:
          obj: style
          None: if no match is found
        """
        result = cls.get().search([('name', '=', name)])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_id(cls, id):
        """
        Searches a style by id

        Args:
          id (int): style.id

        Returns:
          obj: style
          None: if no match is found
        """
        result = cls.get().search([('id', '=', int(id))])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_oid(cls, oid, active=True):
        """
        Searches a style by oid (public api id)

        Args:
          oid (int): style.oid

        Returns:
          obj: style
          None: if no match is found
        """
        result = cls.get().search([
            ('oid', '=', oid),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]
