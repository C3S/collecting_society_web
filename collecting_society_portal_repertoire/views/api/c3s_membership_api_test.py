# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import json
import logging
import uuid

from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.httpexceptions import (
    HTTPUnauthorized,
    HTTPForbidden,
    HTTPServiceUnavailable,
    HTTPInternalServerError
)
from cornice import Service
from colander import (
    MappingSchema,
    SchemaNode,
    String,
    OneOf,
    Email
)

log = logging.getLogger(__name__)

_prefix = 'c3smembership'
_services = [
    'repertoire'
]


def authenticate(request):
    _api_key = request.headers['X-Api-Key']
    # api key not set serverside
    if 'api.c3smembership.api_key' not in request.registry.settings:
        raise HTTPServiceUnavailable()
    if not request.registry.settings['api.c3smembership.api_key']:
        raise HTTPServiceUnavailable()
    # api key not valid
    if _api_key != request.registry.settings['api.c3smembership.api_key']:
        raise HTTPUnauthorized()


# --- methods -----------------------------------------------------------------

def email_registered(email):
    # 2DO: check if email exists in db
    return False


def token_for_email_exists(service, email):
    if service == 'repertoire':
        # 2DO: check if token exists for service and email
        return False
    return True


def generate_token(service, email):
    if service == 'repertoire':
        # 2DO: generate token for service and email
        return str(uuid.uuid4())
    return False


def save_token(service, email, token):
    if service == 'repertoire':
        try:
            # 2DO: save token for service and email
            return True
        except:
            return False
    return False


def token_valid(service, email, token):
    if service == 'repertoire':
        # 2DO: check if token matches token for service and email in db
        if token == 'MEMBER_TOKEN':
            return True
        return False
    return False


# --- service: echo -----------------------------------------------------------

echo = Service(
    name=_prefix + 'echo',
    path=_prefix + '/v1/echo',
    description="echo",
    permission=NO_PERMISSION_REQUIRED,
    environment='development'
)


class EchoSchema(MappingSchema):
    echo = SchemaNode(
        String(),
        location="body",
        type='str'
    )


@echo.post(
    validators=(authenticate),
    schema=EchoSchema)
def post_echo(request):

    # get request params
    content = json.loads(request.body)
    echo = content['echo']

    # return echo
    return {
        'echo': echo
    }


# --- service: is_member ------------------------------------------------------

is_member = Service(
    name=_prefix + 'is_member',
    path=_prefix + '/v1/is_member',
    description="is_member",
    permission=NO_PERMISSION_REQUIRED,
    environment='development'
)


class IsMemberSchema(MappingSchema):
    email = SchemaNode(
        String(),
        location="body",
        type='str',
        validator=Email()
    )


@is_member.post(
    validators=(authenticate),
    schema=IsMemberSchema)
def post_is_member(request):

    # get request params
    content = json.loads(request.body)
    email = content['email']

    # check email
    is_member = False
    if email_registered(email):
        is_member = True

    # return member token
    return {
        'is_member': is_member
    }


# --- service: generate_member_token ------------------------------------------

generate_member_token = Service(
    name=_prefix + 'generate_member_token',
    path=_prefix + '/v1/generate_member_token',
    description="generate_member_token",
    permission=NO_PERMISSION_REQUIRED,
    environment='development'
)


class GenerateMemberTokenSchema(MappingSchema):
    service = SchemaNode(
        String(),
        location="body",
        type='str',
        validator=OneOf(_services)
    )
    email = SchemaNode(
        String(),
        location="body",
        type='str',
        validator=Email()
    )


@generate_member_token.post(
    validators=(authenticate),
    schema=GenerateMemberTokenSchema)
def post_generate_member_token(request):

    # get request params
    content = json.loads(request.body)
    service = content['service']
    email = content['email']

    # check email
    if not email_registered(email):
        raise HTTPForbidden()

    # check member token
    if token_for_email_exists(service, email):
        raise HTTPForbidden()

    # generate member token
    token = generate_token(service, email)
    if not token:
        raise HTTPInternalServerError()

    # save member token
    if not save_token(service, email, token):
        raise HTTPInternalServerError()

    # return member token
    return {
        'token': token
    }

# --- service: search_member --------------------------------------------------

search_member = Service(
    name=_prefix + 'search_member',
    path=_prefix + '/v1/search_member',
    description="search_member",
    permission=NO_PERMISSION_REQUIRED,
    environment='development'
)


class SearchMemberSchema(MappingSchema):
    service = SchemaNode(
        String(),
        location="body",
        type='str',
        validator=OneOf(_services)
    )
    email = SchemaNode(
        String(),
        location="body",
        type='str',
        validator=Email()
    )
    token = SchemaNode(
        String(),
        location="body",
        type='str'
    )


@search_member.post(
    validators=(authenticate),
    schema=SearchMemberSchema)
def post_search_member(request):

    # get request params
    content = json.loads(request.body)
    service = content['service']
    email = content['email']
    token = content['token']

    # check email
    if not email_registered(email):
        raise HTTPForbidden()

    # check member token
    if not token_valid(service, email, token):
        raise HTTPForbidden()

    # return member data
    return {
        'firstname': u'TEST_FIRSTNAME',
        'lastname': u'TEST_LASTNAME',
        'email': email,
        'membership_type': u'normal',
        'payment_received': True,
        'membership_accepted': True,
        'signature_confirmed': True
    }
