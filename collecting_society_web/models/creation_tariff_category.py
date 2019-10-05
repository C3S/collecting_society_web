# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class CreationTariffCategory(Tdb):
    """
    Model wrapper for Tryton model object 'creation-tariff_category'
    """

    __name__ = 'creation-tariff_category'

    @classmethod
    def search_all(cls):
        """
        Fetches all creation tariff categories

        Returns:
          list: creation tariff categories
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    def search(cls, domain, offset=None, limit=None, order=None,
               escape=False):
        """
        Searches creation tariff categories by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          obj: list of creation tariff categories
        """
        # prepare query
        if escape:
            domain = cls.escape_domain(domain)
        # search
        result = cls.get().search(domain, offset, limit, order)
        return result

    @classmethod
    def search_by_id(cls, ctc_id):
        """
        Searches a creation tariff category by creation tariff category id

        Args:
          ctc_id (int): creation_tariff_category.id

        Returns:
          obj: creation tariff category
          None: if no match is found
        """
        result = cls.get().search([
            ('id', '=', ctc_id)
        ])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_oid(cls, oid):
        """
        Searches a creation tariff category by oid (public api id)

        Args:
          oid (int): creation_tariff_category.oid

        Returns:
          obj: creation tariff category
          None: if no match is found
        """
        result = cls.get().search([
            ('oid', '=', oid),
        ])
        if not result:
            return None
        return result[0]

    @classmethod
    def delete(cls, ctcs):
        """
        Deletes creation tariff categories

        Args:
          ctcs (list): creation tariff categories::

            [creation_tariff_category, creation_tariff_category, ...]

        Returns:
          ?
        """
        return cls.get().delete(ctcs)

    @classmethod
    def create(cls, vlist):
        """
        Creates creation tariff categories

        Args:
          vlist (list): list of dicts with attributes to create objects

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created creation tariff categories
          None: if no object was created
        """
        log.debug('create creation tariff categories:\n{}'.format(vlist))
        for values in vlist:
            if 'category' not in values:
                raise KeyError('category is missing')
            if 'creation' not in values:
                raise KeyError('creation is missing')
        result = cls.get().create(vlist)
        return result or None
