# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from portal_web.models import Tdb

log = logging.getLogger(__name__)


class Device(Tdb):
    """
    Model wrapper for Tryton model object 'device'
    """

    __name__ = 'device'

    @classmethod
    def search(cls, domain, offset=None, limit=None, order=None,
               escape=False, active=True):
        """
        Searches devices by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          obj: list of devices
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
    def search_count(cls, domain, escape=False, active=True):
        """
        Counts devices by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          int: number of devices
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
    def search_all(cls, active=True):
        """
        Fetches all Devices

        Returns:
          list: device
          None: if no match is found
        """
        return cls.get().search([('active', 'in', (True, active))])

    @classmethod
    def search_by_id(cls, device_id, active=True):
        """
        Searches an device by device id

        Args:
          device_id (int): device.id

        Returns:
          obj: device
          None: if no match is found
        """
        result = cls.get().search([
            ('id', '=', device_id),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_uuid(cls, device_uuid, active=True):
        """
        Searches an device by device uuid

        Args:
          device_uuid (string): device.uuid

        Returns:
          obj: device
          None: if no match is found
        """
        result = cls.get().search([('uuid', '=', device_uuid)])
        if not result:
            return None
        return result[0]

    @classmethod
    def search_by_name(cls, device_name, active=True):
        """
        Searches devices by device name

        Args:
          device_name (str): device.name

        Returns:
          obj: list of devices
        """
        result = cls.get().search([
            ('name', '=', device_name),
            ('active', 'in', (True, active))
        ])
        return result

    @classmethod
    def belongs_to_current_webuser(cls, request):
        """
        returns all objects that belong to a certain licensee

        Args:
          request (pyramid.request.Request): Current request.

        Returns:
          list: objects that belong to the licensee
          None: if no match is found
        """
        return cls.get().search([('web_user', '=', request.web_user.id)])

    @classmethod
    def delete(cls, device):
        """
        Deletes device

        Args:
          device (list): devices::

            [device1, device2, ...]

        Returns:
          ?
        """
        return cls.get().delete(device)

    @classmethod
    def create(cls, vlist):
        """
        Creates devices

        Args:
          vlist (list): list of dicts with attributes to create devices::

            [
                {
                    'web_user': ...,
                    'uuid': ...,
                    'name': ...,
                    'os_name': ...,
                    'os_version': ...,
                    'software_name': ...,
                    'software_version': ...,
                    'software_vendor': ...
                },
                {
                    ...
                }
            ]

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created devices
          None: if no object was created
        """
        log.debug('create devices:\n{}'.format(vlist))
        for values in vlist:
            if 'name' not in values:
                raise KeyError('name is missing')
        result = cls.get().create(vlist)
        return result or None
