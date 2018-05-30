# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import os
import logging

from pyramid.security import (
    Allow,
    DENY_ALL,
    NO_PERMISSION_REQUIRED
)
# from pyramid.httpexceptions import (
#     HTTPUnauthorized,
#     HTTPForbidden,
#     HTTPServiceUnavailable,
#     HTTPInternalServerError
# )
from cornice import Service
from cornice.validators import colander_body_validator
import colander

from collecting_society_portal.models import Tdb
from ...models import Artist

log = logging.getLogger(__name__)


_prefix = 'datatables'


# --- methods -----------------------------------------------------------------

def get_cors_policy():
    return {
        'origins': os.environ['API_DATATABLES_CORS_ORIGINS'].split(","),
        'credentials': True
    }


def get_cors_headers():
    return ', '.join([
        'content-type',
    ])


# --- schemas -----------------------------------------------------------------

class OrderSchema(colander.MappingSchema):
    column = colander.SchemaNode(
        colander.Integer(), validator=colander.Range(0))
    dir = colander.SchemaNode(
        colander.String(), validator=colander.OneOf(['asc', 'desc']))


class OrdersSchema(colander.SequenceSchema):
    order = OrderSchema()


class SearchSchema(colander.MappingSchema):
    regex = colander.SchemaNode(
        colander.Boolean())
    value = colander.SchemaNode(
        colander.String(), missing="")


class ColumnSchema(colander.MappingSchema):
    data = colander.SchemaNode(
        colander.String(), missing="")
    name = colander.SchemaNode(
        colander.String())
    orderable = colander.SchemaNode(
        colander.Boolean())
    search = SearchSchema()
    searchable = colander.SchemaNode(
        colander.Boolean())


class ColumnsSchema(colander.SequenceSchema):
    column = ColumnSchema()


class DatatablesSchema(colander.MappingSchema):
    columns = ColumnsSchema()
    order = OrdersSchema()
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
                ('read')
            ),
            DENY_ALL
        ]


# --- service: artists --------------------------------------------------------

artists = Service(
    name=_prefix + 'artists',
    path=_prefix + '/v1/artists',
    description="provide artists for datatables",
    cors_policy=get_cors_policy(),
    factory=UserResource
)


@artists.options(
    permission=NO_PERMISSION_REQUIRED)
def options_artists(request):
    response = request.response
    response.headers['Access-Control-Allow-Headers'] = get_cors_headers()
    return response


@artists.post(
    permission='read',
    schema=DatatablesSchema(),
    validators=(colander_body_validator,))
@Tdb.transaction(readonly=False)
def post_artists(request):
    data = request.validated
    # domain
    search = Tdb.escape(data['search']['value'], wrap=True)
    domain = [
        [
            'OR',
            ('code', 'ilike', search),
            ('name', 'ilike', search),
            ('description', 'ilike', search)
        ]
    ]
    for column in data['columns']:
        if not column['searchable'] or not column['search']['value']:
            continue
        if column['name'] in ['name', 'code']:
            search = Tdb.escape(column['search']['value'], wrap=True)
            domain.append((column['name'], 'ilike', search))
        if column['name'] == "group":
            search = (column['search']['value'] == "True")
            domain.append(('group', '=', search))
    # order
    order = []
    order_allowed = ['name', 'code']
    for _order in data['order']:
        name = data['columns'][_order['column']]['name']
        if name in order_allowed:
            order.append((name, _order['dir']))
    # statistics
    total_domain = []
    for column in data['columns']:
        if column['name'] == "group":
            search = (column['search']['value'] == "True")
            total_domain.append(('group', '=', search))
    total = Artist.search_count(total_domain)
    filtered = Artist.search_count(domain)
    # records
    records = []
    for artist in Artist.search(
            domain=domain,
            offset=data['start'],
            limit=data['length'],
            order=order):
        records.append({
            'group': artist.group,
            'name': artist.name,
            'code': artist.code,
            'description': artist.description
        })
    # response
    return {
        'draw': data['draw'],
        'recordsTotal': total,
        'recordsFiltered': filtered,
        'data': records,
    }
