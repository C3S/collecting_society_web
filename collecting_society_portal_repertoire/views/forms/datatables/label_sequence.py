# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import colander
import deform

from collecting_society_portal.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)


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


class LabelSequence(DatatableSequence):
    label_sequence = LabelSchema()
    widget = label_sequence_widget
