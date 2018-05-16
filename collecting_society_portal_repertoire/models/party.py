# For copyright and party terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from collecting_society_portal.models import Tdb

log = logging.getLogger(__name__)


class Party(Tdb):
    """
    Model wrapper for Tryton model object 'party'
    """

    __name__ = 'party.party'

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_all(cls):
        """
        Fetches all Parties

        Returns:
          list: parties
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_name(cls, name):
        """
        Searches a party by name

        Args:
          name (string): party.name

        Returns:
          obj: party
          None: if no match is found
        """
        result = cls.get().search([('name', '=', name)])
        return result[0] or None
