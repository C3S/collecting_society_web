# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import os
import json
import logging

from pyramid.security import (
    Allow,
    DENY_ALL,
    NO_PERMISSION_REQUIRED
)
from pyramid.httpexceptions import (
    HTTPUnauthorized,
    HTTPForbidden,
    HTTPServiceUnavailable,
    HTTPInternalServerError
)
from cornice import Service
#from cornice.validators import colander_body_validator
import colander

from collecting_society_portal.models import Tdb

log = logging.getLogger(__name__)


_prefix = 'datatables'


# --- methods -----------------------------------------------------------------

def get_cors_policy():
    return {
        'origins': os.environ['API_DATATABLES_CORS_ORIGINS'].split(","),
        'credentials': True
    }


# def get_cors_headers():
#     return ', '.join([
#         'Content-Type',
#         'Content-Range',
#         'Content-Disposition',
#         'Content-Description'
#     ])


# --- schemas -----------------------------------------------------------------

class OrderSchema(colander.MappingSchema):
    column = colander.SchemaNode(
        colander.Integer(), validator=colander.Range(0))
    dir = colander.SchemaNode(
        colander.String(), validator=colander.OneOf(['asc', 'desc']))


class SearchSchema(colander.MappingSchema):
    regex = colander.SchemaNode(
        colander.Boolean())
    value = colander.SchemaNode(
        colander.String())


class ColumnSchema(colander.MappingSchema):
    data = colander.SchemaNode(
        colander.Integer(), validator=colander.Range(0))
    name = colander.SchemaNode(
        colander.String())
    orderable = colander.SchemaNode(
        colander.Boolean())
    search = SearchSchema()
    serachable = colander.SchemaNode(
        colander.Boolean())


class ColumnsSchema(colander.SequenceSchema):
    column = ColumnSchema()


class DatatablesSchema(colander.MappingSchema):
    columns = ColumnsSchema()
    order = OrderSchema()
    search = SearchSchema()
    draw = colander.SchemaNode(
        colander.Integer(), validator=colander.Range(0))
    start = colander.SchemaNode(
        colander.Integer(), validator=colander.Range(0))
    length = colander.SchemaNode(
        colander.Integer(), validator=colander.Range(0))


# --- resources ---------------------------------------------------------------

class UserResource(object):

    def __init__(self, request):
        self.request = request

    def __acl__(self):
        # no webuser logged in
        if not self.request.user:
            return [DENY_ALL]
        # webuser logged in
        return [
            (
                Allow,
                self.request.unauthenticated_userid,
                ('create', 'read', 'update', 'delete')
            ),
            DENY_ALL
        ]


# --- service: artists --------------------------------------------------------

artists = Service(
    name=_prefix + 'artists',
    path=_prefix + '/v1/artists',
    description="provide artists for datatables",
    factory=UserResource
)


@artists.post(
    permission='read',
    schema=DatatablesSchema)
@Tdb.transaction(readonly=False)
def post_datatables_artists(request):
    return {
        'test': 'test'
    }
