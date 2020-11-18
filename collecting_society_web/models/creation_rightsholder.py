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
    def search_artist_creation_contribution_and_instrument(cls,
                                                              artist_code,
                                                              creation_code,
                                                              contribution):
        """
        Searches creation.rightsholder by a quadruple of fields

        Args:
          artist_code (int): artist.code
          creation_code (int): creation.code
          contribution (char): "composition", "lyrics", etc.

        Returns:
          list: creations.rightsholder
          None: if no match is found
        """
        result = cls.get().search([
            ('rightsholder_subject.code', '=', artist_code),
            ('rightsholder_object.code', '=', creation_code),
            ('contribution', '=', contribution)
            ])
        return result or None

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