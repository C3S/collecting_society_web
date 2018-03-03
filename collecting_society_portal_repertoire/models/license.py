# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.creative

import logging

from collecting_society_portal.models import Tdb

log = logging.getLogger(__name__)


class License(Tdb):
    """
    Model wrapper for Tryton model object 'license'
    """

    __name__ = 'license'

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_all(cls):
        """
        Fetches all Licenses

        Returns:
          list: licenses
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_id(cls, license_id):
        """
        Searches an license by license id

        Args:
          license_id (int): license.id

        Returns:
          obj: license
          None: if no match is found
        """
        result = cls.get().search([('id', '=', license_id)])
        return result[0] or None
