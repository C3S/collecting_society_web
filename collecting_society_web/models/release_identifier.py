# For copyright and release_identifier terms, see COPYRIGHT.rst (top level of
# repository) Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class ReleaseIdentifier(Tdb):
    """
    Model wrapper for Tryton model object 'release_identifier'
    """

    __name__ = 'release.identifier'

    @classmethod
    def search_all(cls):
        """
        Fetches all ReleaseIdentifiers

        Returns:
          list: release_identifiers
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    def search_by_spacecode(cls, id_space, id_code):
        """
        Searches a release_identifier in certain id_space by given id_code

        .. note::

          This is the preferred method of accessing an identifier.
          Only if ``id_space`` and ``id_code`` are bothe provided,
          an object can be determined with certainty.

        Args:
          id_code (string): release_identifier.id_code
          id_space (string): release_identifier.id_space

        Returns:
          obj: release_identifier
          None: if no match is found
        """
        result = cls.get().search([
          ('space', '=', id_space),
          ('id_code', '=', id_code)
          ])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_code(cls, id_code):
        """
        Searches all foreign release_identifiers for a given native id_code

        .. note::

          This is the preferred method of accessing an identifier.
          Only if ``id_space`` and ``id_code`` are both provided,
          an object can be determined with certainty.

        Args:
          id_code (string): release_identifier.id_code

        Returns:
          obj: release_identifier *list*
          None: if no match is found
        """
        result = cls.get().search([('id_code', '=', id_code)])
        if not result:
            return None
        return result

    @classmethod
    def search_by_id(cls, id):
        """
        Searches a release_identifier by id

        Args:
          id (int): release_identifier.id

        .. note::
          This is a search for the internal database id,
          not the id_code of a certaion id_space.

        Returns:
          obj: release_identifier
          None: if no match is found
        """
        result = cls.get().search([('id', '=', int(id))])
        if not result:
            return None
        return result[0]
