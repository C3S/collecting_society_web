# For copyright and genre terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import (
    Tdb,
    MixinSearchById,
    MixinSearchByOid,
    MixinSearchAll
)

log = logging.getLogger(__name__)


class LocationSpace(Tdb, MixinSearchById, MixinSearchByOid, MixinSearchAll):
    """
    Model wrapper for Tryton model object 'location.space'
    """
    __name__ = 'location.space'

    @classmethod
    def search_count(cls, domain, escape=False, active=True):
        """
        Counts location spaces by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          int: number of location spaces
        """
        # prepare query
        if escape:
            domain = cls.escape(domain)
        if active:
            domain.append(('active', 'in', (True, active)))
        # search
        result = cls.get().search_count(domain)
        return result