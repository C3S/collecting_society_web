# For copyright and label terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from collecting_society_portal.models import Tdb

log = logging.getLogger(__name__)


class CreationDerivative(Tdb):
    """
    Model wrapper for Tryton model object 'creationd_derivative'
    """

    __name__ = 'creation.original.derivative'


    @classmethod
    def create(cls, vlist):
        """
        Creates origina-derivative relations

        Args:
          vlist (list): list of dicts with attributes 
          to create origina-derivative relations::

            [
                {
                    'original_creation': creation.id,
                    'derivative_creation': creation.id,
                    'allocation_type': 'adaption'|'cover'|'remix'
                },
                {
                    ...
                }
            ]

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created origina-derivative relations
          None: if no object was created
        """
        log.debug('create CreationDerivative:\n{}'.format(vlist))
        result = cls.get().create(vlist)
        return result or None

    @classmethod
    def delete(cls, creation):
        """
        Deletes creation(s)

        Args:
          creation (list): creations::

            [creation1, creation2, ...]

        Returns:
          ?
        """
        return cls.get().delete(creation)

    @classmethod
    def search_originals_of_creation_by_id(cls, creation_id):
        """
        Searches all original creations of a creation by its id

        Args:
          creation_id (int): creation.id

        Returns:
          obj: list of creations
          None: if no match is found
        """
        result = cls.get().search(
            [('derivative_creation.id', '=', creation_id)]
        )
        return result or None

    @classmethod
    def search_original_derivative_pair(cls, derivative_oid, original_oid):
        """
        Searches for certain derivative/original combinations

        Args:
          derivative_oid (string) a uuid formed string
          original_oid (string): a uuid formed string

        Returns:
          obj: list of creations
          None: if no match is found
        """
        result = cls.get().search(
            [('original_creation.oid', '=', original_oid),
             ('derivative_creation.oid', '=', derivative_oid)]
        )
        return result or None

    @classmethod
    def search_by_oid(cls, oid):
        """
        Searches for a CreationDerivative object by its oid

        Args:
          oid (string): a uuid formed string

        Returns:
          obj: CreationDerivative object
          None: if no match is found
        """
        result = cls.get().search([('oid', '=', oid)])
        return result[0] or None
