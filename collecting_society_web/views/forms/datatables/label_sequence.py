# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import colander
import deform

from portal_web.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)

from ....models import Label


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
def label_sequence_widget(node, kw):
    # get initial source data
    source_data = []
    domain = []
    labels = Label.search(
        domain=domain,
        offset=0,
        limit=10,
        order=[('name', 'asc')])
    for label in labels:
        source_data.append({
            'oid': label.oid,
            'gvl_code': label.gvl_code,
            'name': label.name})
    # get statistics
    total_domain = []
    total = Label.search_count(total_domain)
    # return widget
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/label_sequence',
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


class GvlCodeField(colander.SchemaNode):
    oid = "gvl_code"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    missing = ""


class NameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


# --- Schemas -----------------------------------------------------------------

class LabelSchema(colander.Schema):
    mode = ModeField()
    oid = OidField()
    name = NameField()
    gvl_code = GvlCodeField()
    preparer = [prepare_required]
    title = ""


class LabelSequence(DatatableSequence):
    label_sequence = LabelSchema()
    widget = label_sequence_widget
