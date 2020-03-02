# For copyright and genre terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import (
    Tdb,
    MixinSearchById,
    MixinSearchByUuid
)

log = logging.getLogger(__name__)


class DeviceMessage(Tdb, MixinSearchById, MixinSearchByUuid):
    """
    Model wrapper for Tryton model object 'device.message'
    """
    __name__ = 'device.message'
