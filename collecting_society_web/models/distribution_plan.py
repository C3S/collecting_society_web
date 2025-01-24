# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class DistributionPlan(Tdb):
    """
    Model wrapper for Tryton model object 'distribution.plan'
    """

    __name__ = 'distribution.plan'

    @classmethod
    def search(cls, domain, offset=None, limit=None, order=None, escape=False):
        """
        Searches distribution plans by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          obj: list of distribution plans
        """
        # prepare query
        if escape:
            domain = cls.escape_domain(domain)
        # search
        result = cls.get().search(domain, offset, limit, order)
        return result

    @classmethod
    def search_latest(cls):
        """
        Searches latest distribution plan

        Returns:
          obj: latest distribution plan
          None: if no match is found
        """
        result = cls.get().search([], 0, 1, [('id', 'DESC')])
        if not result:
            return None
        return result[0]
