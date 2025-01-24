# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class TariffRelevanceCategory(Tdb):
    """
    Model wrapper for Tryton model object
    'tariff_system.tariff.relevance.category'
    """

    __name__ = 'tariff_system.tariff.relevance.category'

    @classmethod
    def search_all(cls):
        """
        Fetches all tariff relevance categories

        Returns:
          list: tariff relevance categories
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    def search_by_oid(cls, oid, active=True):
        """
        Searches a tariff relevance category by oid (public api id)

        Args:
          oid (int): tariff_relevance_category.oid

        Returns:
          obj: tariff_relevance_category
          None: if no match is found
        """
        result = cls.get().search([
            ('oid', '=', oid),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]
