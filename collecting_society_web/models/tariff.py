# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class Tariff(Tdb):
    """
    Model wrapper for Tryton model object 'tariff_system.tariff'
    """

    __name__ = 'tariff_system.tariff'

    @classmethod
    def search_latest_by_category_code(cls, code):
        """
        Searches latest tariff by category code

        Args:
          code (str): tariff category code

        Returns:
          obj: tariff
          None: if no match is found
        """
        result = cls.get().search([('category.code', '=', code)])
        if not result:
            return None
        return result[-1]
