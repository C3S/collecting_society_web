# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class ReleaseIdentifierSpace(Tdb):
    """
    Model wrapper for Tryton model object 'release_identifier_space'
    """

    __name__ = 'release.identifier.space'

    @classmethod
    def search_all(cls):
        """
        Fetches all ReleaseIdentifierSpaces

        Returns:
          list: release_identifier_spaces
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    def search_by_name(cls, name):
        """
        Searches a release_identifier_space by name

        Args:
          name (string): release_identifier_space.name

        Returns:
          obj: release_identifier_space
          None: if no match is found
        """
        result = cls.get().search([('name', '=', name)])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_id(cls, id):
        """
        Searches a release_identifier_space by id

        Args:
          id (int): release_identifier_space.id

        Returns:
          obj: release_identifier_space
          None: if no match is found
        """
        result = cls.get().search([('id', '=', int(id))])
        if not result:
            return None
        return result[0]
