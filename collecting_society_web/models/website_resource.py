# For copyright and genre terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import (
    Tdb,
    MixinSearchById,
    MixinSearchByName,
    MixinSearchByUuid
)

log = logging.getLogger(__name__)


class WebsiteResource(Tdb, MixinSearchById, MixinSearchByName,
                      MixinSearchByUuid):
    """
    Model wrapper for Tryton model object 'website.resource'
    """
    __name__ = 'website.resource'
