# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

import colander
import deform

from portal_web.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget,
)

from ....models import TariffAdjustmentCategory

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


# --- Widgets -----------------------------------------------------------------

@colander.deferred
def tariff_adjustment_sequence_widget(node, kw):
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/tariff_adjustment_sequence',
    )


@colander.deferred
def category_select_widget(node, kw):
    categories = TariffAdjustmentCategory.search_all()
    category_options = [(category.code, category.name)
                        for category in categories
                        if category.code not in [
                            'electronic_submission',
                            'missing_playlist_fee',
                        ]]
    widget = deform.widget.SelectWidget(values=category_options)
    return widget


# --- Fields ------------------------------------------------------------------

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


class CategoryField(colander.SchemaNode):
    oid = "category"
    schema_type = colander.String
    widget = category_select_widget


class StatusField(colander.SchemaNode):
    oid = "status"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    missing = ""


class ValueField(colander.SchemaNode):
    oid = "value"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    missing = ""


# --- Schemas -----------------------------------------------------------------

class TariffAdjustmentSchema(colander.Schema):
    oid = OidField()
    mode = ModeField()
    category = CategoryField()
    value = ValueField()
    status = StatusField()
    preparer = [prepare_required]
    title = ""


class TariffAdjustmentSequence(DatatableSequence):
    tariff_adjustment_sequence = TariffAdjustmentSchema()
    widget = tariff_adjustment_sequence_widget
    actions = ['create']
