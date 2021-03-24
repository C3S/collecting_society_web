# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class CreationRole(Tdb):
    """
    Model wrapper for Tryton model object 'creation.role'
    """

    __name__ = 'creation.role'

    @classmethod
    def search_all(cls):
        """
        Fetches all creation roles

        Returns:
          list: creation roles
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    def search_by_name(cls, name):
        """
        Searches a creation role by name

        Args:
          name (string): creation.role

        Returns:
          obj: creation role
          None: if no match is found
        """
        result = cls.get().search([('name', '=', name)])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_id(cls, id):
        """
        Searches a creation role by id

        Args:
          id (int): creation.role.id

        Returns:
          obj: creation role
          None: if no match is found
        """
        result = cls.get().search([('id', '=', int(id))])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_oid(cls, oid):
        """
        Searches an creation role by oid (public api id)

        Args:
          oid (int): creation.role.oid

        Returns:
          obj: creation role
          None: if no match is found
        """
        result = cls.get().search([
            ('oid', '=', oid)
        ])
        if not result:
            return None
        return result[0]
