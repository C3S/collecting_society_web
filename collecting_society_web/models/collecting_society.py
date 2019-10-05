# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class CollectingSociety(Tdb):
    """
    Model wrapper for Tryton model object 'collecting_society'
    """

    __name__ = 'collecting_society'

    @classmethod
    def search_all(cls):
        """
        Fetches all collecting societies

        Returns:
          list: collecting societies
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    def search(cls, domain, offset=None, limit=None, order=None,
               escape=False, active=True):
        """
        Searches collecting societies by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          obj: list of collecting societies
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
    def search_by_id(cls, collecting_society_id):
        """
        Searches a collecting society by id

        Args:
          collecting_society_id (int): collecting_society.id

        Returns:
          obj: collecting society
          None: if no match is found
        """
        result = cls.get().search([('id', '=', collecting_society_id)])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_oid(cls, oid, active=True):
        """
        Searches a collecting society by oid (public api id)

        Args:
          oid (int): collecting_society.oid

        Returns:
          obj: collecting society
          None: if no match is found
        """
        result = cls.get().search([
            ('oid', '=', oid),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]
