# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging
import requests
from requests import ConnectionError

log = logging.getLogger(__name__)


class C3SMembershipApiClient(object):

    _base_url = None
    _api_key = None

    def __init__(self, base_url, api_key):
        if not base_url.endswith('/'):
            base_url += "/"
        self._base_url = base_url
        self._api_key = api_key

    def send(self, url, data):
        errormsg = "Error in c3s membership api call"

        # request
        try:
            response = requests.post(url, data)

        # response error
        except ConnectionError as ce:
            log.debug(errormsg + ' (ConnectionError): %s' % ce)
            return False
        if not response or 'status' not in response:
            log.debug(
                errormsg + ' (Unknown):\nurl: %s\ndata: %s\nresponse: %s' % (
                    url, data, response
                )
            )
            return False
        if response['status'] is not 200:
            log.debug(
                errormsg + ' (%s):\nurl: %s\ndata: %s\nresponse: %s' % (
                    response['status'], url, data, response
                )
            )
            return False

        # response ok
        return response['data']

    def get_action_url(self, action):
        return self._base_url + action

    # --- Actions -------------------------------------------------------------

    def echo(self, message):
        action = "echo"
        data = {
            'echo': message
        }
        return self.send(
            self.get_action_url(action),
            data
        )

    def generate_member_token(self, service, email):
        action = "generate_member_token"
        data = {
            'service': service,
            'email': email
        }
        return self.send(
            self.get_action_url(action),
            data
        )

    def search_member_by_member_token(self, service, member_token):
        action = "search_member_by_member_token"
        data = {
            'service': service,
            'member_token': member_token
        }
        return self.send(
            self.get_action_url(action),
            data
        )
