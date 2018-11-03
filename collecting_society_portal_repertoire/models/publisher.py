# For copyright and label terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from collecting_society_portal.models import Tdb

log = logging.getLogger(__name__)


class Publisher(Tdb):
    """
    Model wrapper for Tryton model object 'publisher'
    """

    __name__ = 'publisher'

    @classmethod
    def search(cls, domain, offset=None, limit=None, order=None,
               escape=False):
        """
        Searches publisher by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          obj: list of publisher
        """
        # prepare query
        if escape:
            domain = cls.escape_domain(domain)
        # search
        result = cls.get().search(domain, offset, limit, order)
        return result

    @classmethod
    def search_count(cls, domain, escape=False, active=True):
        """
        Counts publisher by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          int: number of publisher
        """
        # prepare query
        if escape:
            domain = cls.escape(domain)
        if active:
            domain.append(('active', 'in', (True, active)))
        # search
        result = cls.get().search_count(domain)
        return result

    @classmethod
    def search_all(cls):
        """
        Fetches all Labels

        Returns:
          list: publisher
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    def search_by_oid(cls, oid, active=True):
        """
        Searches a label by oid (public api id)

        Args:
          oid (int): label.oid

        Returns:
          obj: label
          None: if no match is found
        """
        result = cls.get().search([
            ('oid', '=', oid),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]

    @classmethod
    def create(cls, vlist):
        """
        Creates publisher

        Args:
          vlist (list): list of dicts with attributes to create publisher::

            [
                {
                    'name': str (required)
                },
                {
                    ...
                }
            ]

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created publisher
          None: if no object was created
        """
        log.debug('create publisher:\n{}'.format(vlist))
        for values in vlist:
            if 'name' not in values:
                raise KeyError('name is missing')
        result = cls.get().create(vlist)
        return result or None
