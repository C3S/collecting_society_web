# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from pyramid.security import NO_PERMISSION_REQUIRED
from cornice import Service
from cornice.validators import colander_body_validator

from portal_web.models import Tdb, Party

from . import (
    _prefix,
    get_cors_policy,
    get_cors_headers,
    DatatablesResource,
    DatatablesSchema,
)

log = logging.getLogger(__name__)


# --- schemas -----------------------------------------------------------------

class RightsholderDatatablesSchema(DatatablesSchema):
    pass


# --- service: rightsholder ---------------------------------------------------

rightsholder = Service(
    name=_prefix + 'rightsholder',
    path=_prefix + '/v1/rightsholder',
    description="provide rightsholder for datatables",
    cors_policy=get_cors_policy(),
    factory=DatatablesResource
)


@rightsholder.options(
    permission=NO_PERMISSION_REQUIRED)
def options_rightsholder(request):
    response = request.response
    response.headers['Access-Control-Allow-Headers'] = get_cors_headers()
    return response


@rightsholder.post(
    permission='read',
    schema=RightsholderDatatablesSchema(),
    validators=(colander_body_validator,))
def post_rightsholder(request):
    data = request.validated
    web_user = request.web_user
    # domain
    search = Tdb.escape(data['search']['value'], wrap=True)
    total_domain = [Party.get_rightsholder_domain(web_user)]
    domain = total_domain + [
        [
            'OR',
            ('name', 'ilike', search),
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
    total = Party.search_count_rightsholder(total_domain, web_user=web_user)
    filtered = Party.search_count_rightsholder(domain, web_user=web_user)
    # records
    records = []
    for rightsholder in Party.search_rightsholder(
            domain=domain,
            offset=data['start'],
            limit=data['length'],
            order=order,
            web_user=web_user):
        records.append({
            'oid': rightsholder.oid,
            'name': rightsholder.name,
        })
    # response
    return {
        'draw': data['draw'],
        'recordsTotal': total,
        'recordsFiltered': filtered,
        'data': records,
    }
