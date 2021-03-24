# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import (
    Tdb,
    MixinSearchById,
    MixinSearchByName,
    MixinSearchByCode,
    MixinSearchAll
)

log = logging.getLogger(__name__)


class LocationCategory(Tdb, MixinSearchById, MixinSearchByCode,
                       MixinSearchByName, MixinSearchAll):
    """
    Model wrapper for Tryton model object 'location.category'
    """
    __name__ = 'location.category'
