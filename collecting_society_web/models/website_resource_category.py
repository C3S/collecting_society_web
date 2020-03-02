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


class WebsiteResourceCategory(Tdb, MixinSearchById, MixinSearchByName,
                              MixinSearchByCode):
    """
    Model wrapper for Tryton model object 'website.resource.category'
    """
    __name__ = 'website.resource.category'
