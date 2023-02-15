# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class ArtistIdentifierSpace(Tdb):
    """
    Model wrapper for Tryton model object 'artist_identifier_space'
    """

    __name__ = 'artist.identifier.space'

    @classmethod
    def search_all(cls):
        """
        Fetches all ArtistIdentifierSpaces

        Returns:
          list: artist_identifier_spaces
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    def search_by_name(cls, name):
        """
        Searches a artist_identifier_space by name

        Args:
          name (string): artist_identifier_space.name

        Returns:
          obj: artist_identifier_space
          None: if no match is found
        """
        result = cls.get().search([('name', '=', name)])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_id(cls, id):
        """
        Searches a artist_identifier_space by id

        Args:
          id (int): artist_identifier_space.id

        Returns:
          obj: artist_identifier_space
          None: if no match is found
        """
        result = cls.get().search([('id', '=', int(id))])
        if not result:
            return None
        return result[0]
