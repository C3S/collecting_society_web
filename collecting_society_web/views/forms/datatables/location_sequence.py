# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import colander
import deform

from portal_web.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)
from portal_web.models import Country

from ....models import (
    Location,
    LocationCategory,
)


def prepare_ignored(value):
    # workaround for conditinally required fields, as form validators are not
    # processed, if a normal required field is missing
    return value if value else "IGNORED"


def prepare_required(value):
    # oid required for add/edit
    if value['mode'] != "create" and value['oid'] == "IGNORED":
        value['oid'] = ""
    return value


# --- Widgets -----------------------------------------------------------------

@colander.deferred
def country_select_widget(node, kw):
    countries = Country.search_all()
    country_options = [(country.code, country.name) for country in countries]
    widget = deform.widget.SelectWidget(values=country_options)
    return widget


@colander.deferred
def category_select_widget(node, kw):
    categories = LocationCategory.search_all()
    category_options = [(category.code, category.name)
                        for category in categories]
    widget = deform.widget.SelectWidget(values=category_options)
    return widget


# --- Fields ------------------------------------------------------------------

@colander.deferred
def location_sequence_widget(node, kw):
    request = kw.get('request')
    # get initial source data
    domain = [[
        'OR',
        # public locations
        ('public', '=', True),
        # foreign locations created by webuser
        [('entity_origin', '=', 'indirect'),
         ('entity_creator', '=', request.web_user.party.id)]
    ]]
    locations = Location.search(
        domain=domain,
        offset=0,
        limit=10,
        order=[('name', 'asc')])
    source_data = [{
        'oid': location.oid,
        'name': location.name,
        'category': location.category.code,
        'street': location.street,
        'postal_code': location.postal_code,
        'city': location.city,
        'country': getattr(location.country, 'code', ''),
    } for location in locations]
    # get statistics
    total = Location.search_count(domain)
    # return widget
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/location_sequence',
        source_data=source_data,
        source_data_total=total
    )


class ModeField(colander.SchemaNode):
    oid = "mode"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    validator = colander.OneOf(
        ['add', 'create', 'edit'])


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
    widget = category_select_widget


class StreetField(colander.SchemaNode):
    oid = "street"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


class PostalCodeField(colander.SchemaNode):
    oid = "postal_code"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


class CityField(colander.SchemaNode):
    oid = "city"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


class CountryField(colander.SchemaNode):
    oid = "country"
    schema_type = colander.String
    widget = country_select_widget
    default = "DE"


# --- Schemas -----------------------------------------------------------------

class LocationSchema(colander.Schema):
    mode = ModeField()
    oid = OidField()
    name = NameField()
    category = CategoryField()
    street = StreetField()
    postal_code = PostalCodeField()
    city = CityField()
    country = CountryField()
    preparer = [prepare_required]
    title = ""


class LocationSequence(DatatableSequence):
    location_sequence = LocationSchema()
    widget = location_sequence_widget
