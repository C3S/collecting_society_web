# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from collecting_society_portal.models import Tdb

log = logging.getLogger(__name__)


class CreationContribution(Tdb):
    """
    Model wrapper for Tryton model object 'creation.contribution'
    """

    __name__ = 'creation.contribution'

    @classmethod
    def search_all(cls):
        """
        Fetches all creation contributions

        Returns:
          list: creation.contribution
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    def search_by_id(cls, contribution_id):
        """
        Searches a creation contribution by id

        Args:
          contribution_id (int): contribution.id

        Returns:
          obj: creation.contribution
          None: if no match is found
        """
        result = cls.get().search([
            ('id', '=', contribution_id)
        ])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_oid(cls, oid):
        """
        Searches a creation contribution by oid (public api id)

        Args:
          oid (int): creation.contribution.oid

        Returns:
          obj: creation.contribution
          None: if no match is found
        """
        result = cls.get().search([
            ('oid', '=', oid),
        ])
        if not result:
            return None
        return result[0]

    @classmethod
    def delete(cls, contributions):
        """
        Deletes creation contribution

        Args:
          contributions (list): creation.contribution

        Returns:
          ?
        """
        return cls.get().delete(contributions)

    @classmethod
    def create(cls, vlist):
        """
        Creates creation contributions

        Args:
          vlist (list): list of dicts with attributes to create

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created creation contributions
          None: if no object was created
        """
        log.debug('create contributions:\n{}'.format(vlist))
        for values in vlist:
            if 'creation' not in values:
                raise KeyError('creation is missing')
            if 'type' not in values:
                raise KeyError('type is missing')
        result = cls.get().create(vlist)
        return result or None
