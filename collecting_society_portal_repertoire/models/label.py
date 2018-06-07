# For copyright and label terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from collecting_society_portal.models import Tdb

log = logging.getLogger(__name__)


class Label(Tdb):
    """
    Model wrapper for Tryton model object 'label'
    """

    __name__ = 'label'

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_all(cls):
        """
        Fetches all Labels

        Returns:
          list: labels
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_gvl_code(cls, gvl_code):
        """
        Searches a label by gvl code

        Args:
          gvl_code (string): label.gvl_code

        Returns:
          obj: label
          None: if no match is found
        """
        result = cls.get().search([('gvl_code', '=', gvl_code)])
        return result[0] or None

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_name_starting_with(cls, name_starting_with):
        """
        Searches a label for a name starting with certaion characters

        Args:
          name_starting_with (string): label.name

        Returns:
          obj: label
          None: if no match is found
        """
        result = cls.get().search(  # noqa
            [('name', 'like', name_starting_with + '\%')])
        return result[0] or None
