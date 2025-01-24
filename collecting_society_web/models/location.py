# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import (
    Tdb,
    MixinSearchById,
    MixinSearchByOid,
    MixinSearchAll
)

log = logging.getLogger(__name__)


class Location(Tdb, MixinSearchById, MixinSearchByOid, MixinSearchAll):
    """
    Model wrapper for Tryton model object 'location'
    """
    __name__ = 'location'

    @classmethod
    def search(cls, domain, offset=None, limit=None, order=None,
               escape=False):
        """
        Searches location by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          obj: list of locations
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
        Counts location by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          int: number of locations
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
    def search_by_entity_creator(cls, party_id, active=True):
        """
        Searches locations, the web_user is allowed to view.

        Args:
          web_user_id (int): web.user.id

        Returns:
          list: viewable creations of web_user, empty if none were found
        """
        return cls.get().search([
            ('entity_creator.id', '=', party_id),
            ('active', 'in', (True, active))
        ])

    @classmethod
    def create(cls, vlist):
        """
        Creates location

        Args:
          vlist (list): list of dicts with attributes to create location::

            [
                {
                    'name': str (required)
                    'entity_creator': int (required)
                    'entity_origin': 'direct' | 'indirect'
                },
                {
                    ...
                }
            ]

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created location
          None: if no object was created
        """
        log.debug('create location:\n{}'.format(vlist))
        for values in vlist:
            if 'name' not in values:
                raise KeyError('name is missing')
            if 'entity_creator' not in values:
                raise KeyError('entity_creator is missing')
            if ('longitude' in values) != ('latitude' in values):
                raise KeyError('Missing value in latitude/longitude geoinfo '
                               'pair')
        result = cls.get().create(vlist)
        return result or None

    @classmethod
    def delete(cls, location):
        """
        Deletes location

        Args:
          location (list): locations::

            [location1, location2, ...]

        Returns:
          ?
        """
        return cls.get().delete(location)
