# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from pyramid.security import NO_PERMISSION_REQUIRED
from cornice import Service
from cornice.validators import colander_body_validator
import colander

from portal_web.models import Tdb

from ....models import Content
from ....services import _
from pyramid.i18n import get_localizer
from . import (
    _prefix,
    get_cors_policy,
    get_cors_headers,
    DatatablesResource,
    DatatablesSchema,
)

log = logging.getLogger(__name__)


# --- options -----------------------------------------------------------------


# --- schemas -----------------------------------------------------------------

class ContentDatatablesSchema(DatatablesSchema):
    category = colander.SchemaNode(colander.String(), missing="")


# --- service: content -------------------------------------------------------

content = Service(
    name=_prefix + 'content',
    path=_prefix + '/v1/content',
    description="provide contents for datatables",
    cors_policy=get_cors_policy(),
    factory=DatatablesResource
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
def post_content(request):
    data = request.validated
    # domain
    search = Tdb.escape(data['search']['value'], wrap=True)
    domain = [
        [
            'OR',
            ('code', 'ilike', search),
            ('name', 'ilike', search)
        ],
        ('entity_creator', '=', request.web_user.party.id),  # only own
        ('creation', '=', None)                              # only orphaned
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
    if 'category' in data:
        domain.append(('category', '=', data['category']))
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
    total_domain = [
        ('entity_creator', '=', request.web_user.party.id),  # only own
        ('creation', '=', None)                              # only orphaned
    ]
    if 'category' in data:
        total_domain.append(('category', '=', data['category']))
    total = Content.search_count(total_domain)
    filtered = Content.search_count(domain)
    # localization
    locale = get_localizer(request)
    locale_domain = 'collecting_society_web'
    content_category = {
        'audio': locale.translate(_('Audio', locale_domain)),
        'sheet': locale.translate(_('Sheet Music', locale_domain)),
        'lyrics': locale.translate(_('Lyrics', locale_domain)),
    }
    # records
    records = []
    for content in Content.search(
            domain=domain,
            offset=data['start'],
            limit=data['length'],
            order=order):
        records.append({
            'oid': content.oid,
            'name': content.name,
            'code': content.code,
            'category': content_category[content.category],
        })
    # response
    return {
        'draw': data['draw'],
        'recordsTotal': total,
        'recordsFiltered': filtered,
        'data': records,
    }
