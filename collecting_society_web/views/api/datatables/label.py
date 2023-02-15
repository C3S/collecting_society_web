# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from pyramid.security import NO_PERMISSION_REQUIRED
from cornice import Service
from cornice.validators import colander_body_validator

from portal_web.models import Tdb

from ....models import Label
from . import (
    _prefix,
    get_cors_policy,
    get_cors_headers,
    DatatablesResource,
    DatatablesSchema,
)

log = logging.getLogger(__name__)


# --- schemas -----------------------------------------------------------------

class LabelDatatablesSchema(DatatablesSchema):
    pass


# --- service: label ----------------------------------------------------------

label = Service(
    name=_prefix + 'label',
    path=_prefix + '/v1/label',
    description="provide labels for datatables",
    cors_policy=get_cors_policy(),
    factory=DatatablesResource
)


@label.options(
    permission=NO_PERMISSION_REQUIRED)
def options_label(request):
    response = request.response
    response.headers['Access-Control-Allow-Headers'] = get_cors_headers()
    return response


@label.post(
    permission='read',
    schema=LabelDatatablesSchema(),
    validators=(colander_body_validator,))
def post_label(request):
    data = request.validated
    # domain
    search = Tdb.escape(data['search']['value'], wrap=True)
    domain = [
        [
            'OR',
            ('gvl_code', 'ilike', search),
            ('name', 'ilike', search)
        ]
    ]
    for column in data['columns']:
        if not column['searchable'] or not column['search']['value']:
            continue
        if column['name'] in ['name', 'gvl_code']:
            search = Tdb.escape(column['search']['value'], wrap=True)
            domain.append((column['name'], 'ilike', search))
    # order
    order = []
    order_allowed = ['gvl_code', 'name']
    for _order in data['order']:
        name = data['columns'][_order['column']]['name']
        if name in order_allowed:
            order.append((name, _order['dir']))
    # statistics
    total_domain = []
    total = Label.search_count(total_domain)
    filtered = Label.search_count(domain)
    # records
    records = []
    for label in Label.search(
            domain=domain,
            offset=data['start'],
            limit=data['length'],
            order=order):
        records.append({
            'oid': label.oid,
            'gvl_code': label.gvl_code,
            'name': label.name
        })
    # response
    return {
        'draw': data['draw'],
        'recordsTotal': total,
        'recordsFiltered': filtered,
        'data': records,
    }
