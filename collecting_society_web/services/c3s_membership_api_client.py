# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import uuid
import requests
from requests import ConnectionError

log = logging.getLogger(__name__)


class C3SMembershipApiClient(object):

    _url = None
    _api_key = None

    def __init__(self, base_url, version, api_key):
        if not base_url.endswith('/'):
            base_url += "/"
        if not version.endswith('/'):
            version += "/"
        self._url = base_url + version
        self._api_key = api_key

    def send(self, url, data):
        errormsg = "Error in c3s membership api call"
        headers = {'X-Api-Key': self._api_key}

        # request
        try:
            response = requests.post(url, headers=headers, json=data)

        # response error
        except ConnectionError as ce:
            log.debug(errormsg + ' (ConnectionError): %s' % ce)
            return False
        if response.status_code is not 200:
            log.debug(
                errormsg + ' (%s):\nurl: %s\ndata: %s\nresponse: %s' % (
                    response.status_code, url, data, response.reason
                )
            )
            return False

        # response ok
        return response.json()

    def get_action_url(self, action):
        return self._url + action

    def is_connected(self):
        message = str(uuid.uuid4())
        response = self.echo(message)
        if response and response['echo'] == message:
            return True
        return False

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

    def is_member(self, service, email):
        action = "is_member"
        data = {
            'service': service,
            'email': email
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

    def search_member(self, service, email, token):
        action = "search_member"
        data = {
            'service': service,
            'email': email,
            'token': token
        }
        return self.send(
            self.get_action_url(action),
            data
        )
