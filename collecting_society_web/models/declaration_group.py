# For copyright and genre terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb, MixinSearchById, MixinSearchByName

log = logging.getLogger(__name__)


class DeclarationGroup(Tdb, MixinSearchById, MixinSearchByName):
    """
    Model wrapper for Tryton model object 'declaration.group'
    """
    __name__ = 'declaration.group'
