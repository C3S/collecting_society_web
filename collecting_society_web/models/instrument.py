# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import (
    Tdb,
    MixinSearchById,
    MixinSearchByOid,
    MixinSearchAll
)
log = logging.getLogger(__name__)


class Instrument(Tdb, MixinSearchById, MixinSearchByOid, MixinSearchAll):
    """
    Model wrapper for Tryton model object 'instrument'
    """

    __name__ = 'instrument'
