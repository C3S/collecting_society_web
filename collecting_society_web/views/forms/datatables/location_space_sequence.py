# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

import colander
import deform
from pyramid.i18n import get_localizer

from portal_web.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)

from ....services import _
from ....models import (
    LocationSpace,
    LocationSpaceCategory
)

log = logging.getLogger(__name__)


def prepare_ignored(value):
    # workaround for conditinally required fields, as form validators are not
    # processed, if a normal required field is missing
    return value if value else "IGNORED"


def prepare_required(value):
    # oid required for add/edit
    if value['mode'] != "create" and value['oid'] == "IGNORED":
        value['oid'] = ""
    return value


# --- Fields ------------------------------------------------------------------

@colander.deferred
def location_space_sequence_widget(node, kw):
    request = kw.get('request')
    # return widget
    return DatatableSequenceWidget(
        request=request,
        template='datatables/location_space_sequence',
        # source_data=source_data,
        # source_data_total=total
    )


@colander.deferred
def location_space_sequence_widget_thomas(node, kw):
    request = kw.get('request')
    # translation strings
    request.name_translation = get_localizer(
        request).translate(
            _(u'Name', 'collecting_society_web'))
    request.category_translation = get_localizer(
        request).translate(
            _(u'Category', 'collecting_society_web'))
    locale = get_localizer(request)
    locale_domain = 'collecting_society_web'
    location_space_category = {
        'Dancing': locale.translate(_(u'Dancing', locale_domain)),
        'Concert': locale.translate(_(u'Concert', locale_domain)),
        'Waiting': locale.translate(_(u'Waiting', locale_domain)),
        'Shopping': locale.translate(_(u'Shopping', locale_domain)),
        'Eating': locale.translate(_(u'Eating', locale_domain)),
    }
    # get initial source data
    source_data = []
    domain = [
        # ('entity_creator', '=', request.web_user.party.id),  # only own
        # ('creation', '=', None)                              # only orphaned
    ]
    location_spaces = LocationSpace.search_all(
    #    domain=domain,
    #    offset=0,
    #    limit=10,
    #    order=[('name', 'asc')]
    )
    for location_space in location_spaces:
        source_data.append({
            'oid': location_space.oid,
            'name': location_space.name,
            'category': location_space_category[location_space.category.name]})
    # get statistics
    total_domain = [
    #    ('entity_creator', '=', request.web_user.party.id),  # only own
    #    ('creation', '=', None)                              # only orphaned
    ]
    if getattr(node, 'category', None):
        total_domain.append(('category', '=', node.category))
    total = LocationSpace.search_count(total_domain)
    # return widget
    return DatatableSequenceWidget(
        request=request,
        template='datatables/location_space_sequence',
        source_data=source_data,
        source_data_total=total
    )


@colander.deferred
def deferred_location_space_category_widget(node, kw):
    values = [(sc.code, sc.name) for sc in LocationSpaceCategory.search_all()]
    return deform.widget.Select2Widget(values=values)


class ModeField(colander.SchemaNode):
    oid = "mode"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    validator = colander.OneOf(
        ['create', 'edit'])


class OidField(colander.SchemaNode):
    oid = "oid"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    preparer = [prepare_ignored]
    validator = colander.Any(
        colander.uuid,
        colander.Regex(r'^IGNORED\Z', '')
    )


class NameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


class CategoryField(colander.SchemaNode):
    oid = "category"
    schema_type = colander.String
    widget = deferred_location_space_category_widget


class SizeField(colander.SchemaNode):
    oid = "size"
    schema_type = colander.Integer
    validator = colander.Range(1, 1000000)
    widget = deform.widget.TextInputWidget()


class SizeEstimatedField(colander.SchemaNode):
    oid = "size_estimated"
    schema_type = colander.Boolean
    missing = False


# --- Schemas -----------------------------------------------------------------


class LocationSpaceSchema(colander.Schema):
    mode = ModeField()
    oid = OidField()
    name = NameField()
    category = CategoryField()
    size = SizeField()
    size_estimated = SizeEstimatedField(title=_(u'Size only estimated'))
    preparer = [prepare_required]
    title = ""


class LocationSpaceSequence(DatatableSequence):
    location_space_sequence = LocationSpaceSchema()
    widget = location_space_sequence_widget
    actions = ['create', 'edit']
