# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class EventIndicators(Tdb):
    """
    Model wrapper for Tryton model object 'event.indicators'
    """

    __name__ = 'event.indicators'
