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

from ....models import Content
from . import (
    _prefix,
    get_cors_policy,
    get_cors_headers,
    DatatablesResource,
    DatatablesSchema,
)

log = logging.getLogger(__name__)


# --- schemas -----------------------------------------------------------------

class ContentDatatablesSchema(DatatablesSchema):
    pass


# --- resources ---------------------------------------------------------------

class ContentResource(DatatablesResource):
    pass


# --- service: content -------------------------------------------------------

content = Service(
    name=_prefix + 'content',
    path=_prefix + '/v1/content',
    description="provide contents for datatables",
    cors_policy=get_cors_policy(),
    factory=ContentResource
)


@content.options(
    permission=NO_PERMISSION_REQUIRED)
def options_content(request):
    response = request.response
    response.headers['Access-Control-Allow-Headers'] = get_cors_headers()
    return response


@content.post(
    permission='read',
    schema=ContentDatatablesSchema(),
    validators=(colander_body_validator,))
@Tdb.transaction(readonly=True)
def post_content(request):
    data = request.validated
    # domain
    search = Tdb.escape(data['search']['value'], wrap=True)
    domain = [
        [
            'OR',
            ('code', 'ilike', search),
            ('name', 'ilike', search)
        ]
    ]
    for column in data['columns']:
        if not column['searchable'] or not column['search']['value']:
            continue
        if column['name'] == 'code':
            search = Tdb.escape(column['search']['value'], wrap=True)
            domain.append(('code', 'ilike', search))
        if column['name'] == 'name':
            search = Tdb.escape(column['search']['value'], wrap=True)
            domain.append(('name', 'ilike', search))
        if column['name'] == 'category':
            search = Tdb.escape(column['search']['value'], wrap=True)
            domain.append(('category', 'ilike', search))
    # order
    order = []
    for _order in data['order']:
        name = data['columns'][_order['column']]['name']
        if name == 'code':
            order.append(('code', _order['dir']))
        if name == 'name':
            order.append(('name', _order['dir']))
        if name == 'category':
            order.append(('category', _order['dir']))
    # statistics
    total_domain = []
    total = Content.search_count(total_domain)
    filtered = Content.search_count(domain)
    # records
    records = []
    for content in Content.search(
            domain=domain,
            offset=data['start'],
            limit=data['length'],
            order=order):
        records.append({
            'name': content.name,
            'code': content.code,
            'category': content.category,
        })
    # response
    return {
        'draw': data['draw'],
        'recordsTotal': total,
        'recordsFiltered': filtered,
        'data': records,
    }
