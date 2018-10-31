# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import colander
import deform

from collecting_society_portal.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)


def oid_ignored(value):
    return value if value else "OIDIGNORED"


def oid_required_conditionally(value):
    if value['mode'] != "add" and value['oid'] == "OIDIGNORED":
        value['oid'] = ""
    return value


# --- Fields ------------------------------------------------------------------

@colander.deferred
def label_sequence_widget(node, kw):
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/label_sequence'
    )


class ModeField(colander.SchemaNode):
    oid = "mode"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    validator = colander.OneOf(['add', 'create', 'edit'])


class OidField(colander.SchemaNode):
    oid = "oid"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    preparer = [oid_ignored]


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
    name = NameField()
    gvl_code = GvlCodeField()
    title = ""
    preparer = [
        oid_required_conditionally,
    ]


class LabelSequence(DatatableSequence):
    label_sequence = LabelSchema()
    widget = label_sequence_widget
