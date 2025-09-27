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

    @classmethod
    def search(cls, domain, offset=None, limit=None, order=None,
               escape=False, active=True):
        """
        Searches location categories by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          obj: list of location categories
        """
        # prepare query
        if escape:
            domain = cls.escape_domain(domain)
        if active:
            domain.append(('active', 'in', (True, active)))
        # search
        result = cls.get().search(domain, offset, limit, order)
        return result

    @classmethod
    def search_all(cls, active=True):
        """
        Fetches all location categories

        Args:
          active (bool, optional): active records only? Defaults to True.

        Returns:
          list: location categories
          None: if no match is found
        """
        return cls.get().search([('active', 'in', (True, active))])
