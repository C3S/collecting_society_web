# For copyright and genre terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class CreationRightsholder(Tdb):
    """
    Model wrapper for Tryton model object 'creation.rightsholder'
    """
    __name__ = 'creation.rightsholder'

    @classmethod
    def search(cls, domain, offset=None, limit=None, order=None,
               escape=False):
        """
        Searches creation rightsholders by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          obj: list of creation rightsholders
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
        Counts creation rightsholders by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          int: number of creation rightsholders
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
    def create(cls, vlist):
        """
        Creates creation.rightsholder relations

        Args:
          vlist (list): list of dicts with attributes 
          to create creation.rightsholder relations::

            [
                {
                    'rightsholder_subject': rightsholder_subject.id,
                    'rightsholder_object': creation.id,
                    'right': "copyright",
                    'contribution': "production",
                    'instruments': instruments_dict,
                },
                {
                    ...
                }
            ]

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created creation.rightsholder relations
          None: if no object was created
        """
        log.debug('create CreationRightsholder:\n{}'.format(vlist))
        result = cls.get().create(vlist)
        return result or None