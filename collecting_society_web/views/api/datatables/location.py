# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from pyramid.security import NO_PERMISSION_REQUIRED
from cornice import Service
from cornice.validators import colander_body_validator

from portal_web.models import Tdb

from ....models import Location
from . import (
    _prefix,
    get_cors_policy,
    get_cors_headers,
    DatatablesResource,
    DatatablesSchema,
)

log = logging.getLogger(__name__)


# --- schemas -----------------------------------------------------------------

class LocationDatatablesSchema(DatatablesSchema):
    pass


# --- service: location -------------------------------------------------------

location = Service(
    name=_prefix + 'location',
    path=_prefix + '/v1/location',
    description="provide locations for datatables",
    cors_policy=get_cors_policy(),
    factory=DatatablesResource
)


@location.options(
    permission=NO_PERMISSION_REQUIRED)
def options_artist(request):
    response = request.response
    response.headers['Access-Control-Allow-Headers'] = get_cors_headers()
    return response


@location.post(
    permission='read',
    schema=LocationDatatablesSchema(),
    validators=(colander_body_validator,))
def post_artist(request):
    data = request.validated
    # domain
    search = Tdb.escape(data['search']['value'], wrap=True)
    total_domain = [[
        'OR',
        # public locations
        ('public', '=', True),
        # foreign locations created by webuser
        [('entity_origin', '=', 'indirect'),
         ('entity_creator', '=', request.web_user.party.id)]
    ]]
    domain = total_domain + [
        [
            'OR',
            ('name', 'ilike', search),
            ('street', 'ilike', search),
            ('city', 'ilike', search),
        ]
    ]
    for column in data['columns']:
        if not column['searchable'] or not column['search']['value']:
            continue
        if column['name'] in ['name', 'street', 'city']:
            search = Tdb.escape(column['search']['value'], wrap=True)
            domain.append((column['name'], 'ilike', search))
    # order
    order = []
    order_allowed = ['name', 'street', 'city']
    for _order in data['order']:
        name = data['columns'][_order['column']]['name']
        if name in order_allowed:
            order.append((name, _order['dir']))
    # statistics
    total = Location.search_count(total_domain)
    filtered = Location.search_count(domain)
    # records
    records = []
    for location in Location.search(
            domain=domain,
            offset=data['start'],
            limit=data['length'],
            order=order):
        records.append({
            'oid': location.oid,
            'name': location.name,
            'category': location.category.code,
            'street': location.street,
            'postal_code': location.postal_code,
            'city': location.city,
            'country': getattr(location.country, 'code', ''),
        })
    # response
    return {
        'draw': data['draw'],
        'recordsTotal': total,
        'recordsFiltered': filtered,
        'data': records,
    }
