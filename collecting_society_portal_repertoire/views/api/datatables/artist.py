# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

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

from ....models import Artist
from . import (
    _prefix,
    get_cors_policy,
    get_cors_headers,
    DatatablesResource,
    DatatablesSchema,
)

log = logging.getLogger(__name__)


# --- schemas -----------------------------------------------------------------

class ArtistDatatablesSchema(DatatablesSchema):
    group = colander.SchemaNode(colander.Boolean(), missing="")


# --- resources ---------------------------------------------------------------

class ArtistResource(DatatablesResource):
    pass


# --- service: artist --------------------------------------------------------

artist = Service(
    name=_prefix + 'artist',
    path=_prefix + '/v1/artist',
    description="provide artist for datatables",
    cors_policy=get_cors_policy(),
    factory=ArtistResource
)


@artist.options(
    permission=NO_PERMISSION_REQUIRED)
def options_artist(request):
    response = request.response
    response.headers['Access-Control-Allow-Headers'] = get_cors_headers()
    return response


@artist.post(
    permission='read',
    schema=ArtistDatatablesSchema(),
    validators=(colander_body_validator,))
@Tdb.transaction(readonly=False)
def post_artist(request):
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
    if 'group' in data:
        domain.append(('group', '=', data['group']))
    # order
    order = []
    order_allowed = ['name', 'code']
    for _order in data['order']:
        name = data['columns'][_order['column']]['name']
        if name in order_allowed:
            order.append((name, _order['dir']))
    # statistics
    total_domain = []
    if 'group' in data:
        total_domain.append(('group', '=', data['group']))
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
            'name': artist.name,
            'code': artist.code,
            'description': artist.description,
            'email': ""
        })
    # response
    return {
        'draw': data['draw'],
        'recordsTotal': total,
        'recordsFiltered': filtered,
        'data': records,
    }
