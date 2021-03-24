# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class Genre(Tdb):
    """
    Model wrapper for Tryton model object 'genre'
    """

    __name__ = 'genre'

    @classmethod
    def search_all(cls):
        """
        Fetches all Genres

        Returns:
          list: genres
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    def search_by_name(cls, name):
        """
        Searches a genre by name

        Args:
          name (string): genre.name

        Returns:
          obj: genre
          None: if no match is found
        """
        result = cls.get().search([('name', '=', name)])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_id(cls, id):
        """
        Searches a genre by id

        Args:
          id (int): genre.id

        Returns:
          obj: genre
          None: if no match is found
        """
        result = cls.get().search([('id', '=', int(id))])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_oid(cls, oid, active=True):
        """
        Searches an genre by oid (public api id)

        Args:
          oid (int): genre.oid

        Returns:
          obj: genre
          None: if no match is found
        """
        result = cls.get().search([
            ('oid', '=', oid),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]
