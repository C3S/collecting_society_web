# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from pyramid.security import NO_PERMISSION_REQUIRED
from cornice import Service
from cornice.validators import colander_body_validator

from portal_web.models import Tdb

from ....models import Creation
from . import (
    _prefix,
    get_cors_policy,
    get_cors_headers,
    DatatablesResource,
    DatatablesSchema,
)

log = logging.getLogger(__name__)


# --- schemas -----------------------------------------------------------------

class CreationDatatablesSchema(DatatablesSchema):
    pass


# --- service: creation -------------------------------------------------------

creation = Service(
    name=_prefix + 'creation',
    path=_prefix + '/v1/creation',
    description="provide creations for datatables",
    cors_policy=get_cors_policy(),
    factory=DatatablesResource
)


@creation.options(
    permission=NO_PERMISSION_REQUIRED)
def options_creation(request):
    response = request.response
    response.headers['Access-Control-Allow-Headers'] = get_cors_headers()
    return response


@creation.post(
    permission='read',
    schema=CreationDatatablesSchema(),
    validators=(colander_body_validator,))
def post_creation(request):
    data = request.validated
    # domain
    search = Tdb.escape(data['search']['value'], wrap=True)
    domain = [
        [
            'OR',
            ('code', 'ilike', search),
            # ('releases.title', 'ilike', search),
            ('title', 'ilike', search)
        ]
    ]
    for column in data['columns']:
        if not column['searchable'] or not column['search']['value']:
            continue
        if column['name'] == 'code':
            search = Tdb.escape(column['search']['value'], wrap=True)
            domain.append(('code', 'ilike', search))
        if column['name'] == 'titlefield':
            search = Tdb.escape(column['search']['value'], wrap=True)
            domain.append(('title', 'ilike', search))
        if column['name'] == 'artist':
            search = Tdb.escape(column['search']['value'], wrap=True)
            domain.append(('artist.name', 'ilike', search))
        # if column['name'] == 'name':
        #     search = Tdb.escape(column['search']['value'], wrap=True)
        #     domain.append(('releases.title', 'ilike', search))
    # order
    order = []
    for _order in data['order']:
        name = data['columns'][_order['column']]['name']
        if name == 'code':
            order.append(('code', _order['dir']))
        if name == 'titlefield':
            order.append(('title', _order['dir']))
        if name == 'artist':
            order.append(('artist', _order['dir']))
        # if name == 'code':
        #     order.append(('releases.title', _order['dir']))
    # statistics
    total_domain = []
    total = Creation.search_count(total_domain)
    filtered = Creation.search_count(domain)
    # records
    records = []
    for creation in Creation.search(
            domain=domain,
            offset=data['start'],
            limit=data['length'],
            order=order):
        records.append({
            'oid': creation.oid,
            'titlefield': creation.title,
            'artist': creation.artist.name,
            'code': creation.code,
        })
    # response
    return {
        'draw': data['draw'],
        'recordsTotal': total,
        'recordsFiltered': filtered,
        'data': records,
    }
