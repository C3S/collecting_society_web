# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

from pyramid.security import NO_PERMISSION_REQUIRED
from cornice import Service
from cornice.validators import colander_body_validator

from collecting_society_portal.models import Tdb

from ....models import Publisher
from . import (
    _prefix,
    get_cors_policy,
    get_cors_headers,
    DatatablesResource,
    DatatablesSchema,
)

log = logging.getLogger(__name__)


# --- schemas -----------------------------------------------------------------

class PublisherDatatablesSchema(DatatablesSchema):
    pass


# --- service: publisher ------------------------------------------------------

publisher = Service(
    name=_prefix + 'publisher',
    path=_prefix + '/v1/publisher',
    description="provide publishers for datatables",
    cors_policy=get_cors_policy(),
    factory=DatatablesResource
)


@publisher.options(
    permission=NO_PERMISSION_REQUIRED)
def options_publisher(request):
    response = request.response
    response.headers['Access-Control-Allow-Headers'] = get_cors_headers()
    return response


@publisher.post(
    permission='read',
    schema=PublisherDatatablesSchema(),
    validators=(colander_body_validator,))
def post_publisher(request):
    data = request.validated
    # domain
    search = Tdb.escape(data['search']['value'], wrap=True)
    domain = [
        [
            'OR',
            ('name', 'ilike', search)
        ]
    ]
    for column in data['columns']:
        if not column['searchable'] or not column['search']['value']:
            continue
        if column['name'] in ['name']:
            search = Tdb.escape(column['search']['value'], wrap=True)
            domain.append((column['name'], 'ilike', search))
    # order
    order = []
    order_allowed = ['name']
    for _order in data['order']:
        name = data['columns'][_order['column']]['name']
        if name in order_allowed:
            order.append((name, _order['dir']))
    # statistics
    total_domain = []
    total = Publisher.search_count(total_domain)
    filtered = Publisher.search_count(domain)
    # records
    records = []
    for publisher in Publisher.search(
            domain=domain,
            offset=data['start'],
            limit=data['length'],
            order=order):
        records.append({
            'oid': publisher.oid,
            'name': publisher.name
        })
    # response
    return {
        'draw': data['draw'],
        'recordsTotal': total,
        'recordsFiltered': filtered,
        'data': records,
    }
