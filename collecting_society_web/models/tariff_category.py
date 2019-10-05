# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class TariffCategory(Tdb):
    """
    Model wrapper for Tryton model object 'tariff_system.category'
    """

    __name__ = 'tariff_system.category'

    @classmethod
    def search_all(cls):
        """
        Fetches all tariff categories

        Returns:
          list: tariff categories
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    def search_by_id(cls, category_id):
        """
        Searches a tariff category by id

        Args:
          category_id (int): tariff_category.id

        Returns:
          obj: tariff category
          None: if no match is found
        """
        result = cls.get().search([('id', '=', category_id)])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_oid(cls, oid, active=True):
        """
        Searches a tariff category by oid (public api id)

        Args:
          oid (int): tariff_category.oid

        Returns:
          obj: tariff category
          None: if no match is found
        """
        result = cls.get().search([
            ('oid', '=', oid),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]
