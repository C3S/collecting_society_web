# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class License(Tdb):
    """
    Model wrapper for Tryton model object 'license'
    """

    __name__ = 'license'

    @classmethod
    def search_all(cls):
        """
        Fetches all Licenses

        Returns:
          list: licenses
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
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
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_oid(cls, oid, active=True):
        """
        Searches a license by oid (public api id)

        Args:
          oid (int): license.oid

        Returns:
          obj: license
          None: if no match is found
        """
        result = cls.get().search([
            ('oid', '=', oid),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]
