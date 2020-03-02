# For copyright and genre terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import (
    Tdb,
    MixinSearchById,
    MixinSearchByName,
    MixinSearchByCode
)

log = logging.getLogger(__name__)


class LocationSpaceCategory(Tdb, MixinSearchById, MixinSearchByCode, 
                            MixinSearchByName):
    """
    Model wrapper for Tryton model object 'location.space.category'
    """
    __name__ = 'location.space.category'
