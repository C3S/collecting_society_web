# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class TariffAdjustmentCategory(Tdb):
    """
    Model wrapper for Tryton model object
    'tariff_system.tariff.adjustment.category'
    """

    __name__ = 'tariff_system.tariff.adjustment.category'

    @classmethod
    def search_all(cls):
        """
        Fetches all tariff adjustment categories

        Returns:
          list: tariff adjustment categories
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    def search_by_code(cls, code, tariff_category_code, active=True):
        """
        Searches a tariff adjustment category for a tariff by code

        Args:
          code (str): tariff_adjustment_category.code
          tariff_category_code (str): tariff_category.code

        Returns:
          obj: tariff_adjustment_category
          None: if no match is found
        """
        result = cls.get().search([
            ('code', '=', code),
            ('tariff_categories.code', '=', tariff_category_code),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]
