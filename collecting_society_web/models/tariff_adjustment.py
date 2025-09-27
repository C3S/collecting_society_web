# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class TariffAdjustment(Tdb):
    """
    Model wrapper for Tryton model object 'tariff_system.tariff.adjustment'
    """

    __name__ = 'tariff_system.tariff.adjustment'
