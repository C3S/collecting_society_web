# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class TariffRelevance(Tdb):
    """
    Model wrapper for Tryton model object 'tariff_system.tariff.relevance'
    """

    __name__ = 'tariff_system.tariff.relevance'

    @classmethod
    def search_by_oid(cls, oid, active=True):
        """
        Searches a tariff relevance by oid

        Args:
          oid (int): tariff_relevance.oid

        Returns:
          obj: tariff relevance
          None: if no match is found
        """
        result = cls.get().search([
            ('oid', '=', oid),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]
