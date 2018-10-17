# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

import colander
import deform

from collecting_society_portal.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)

log = logging.getLogger(__name__)


# --- Fields ------------------------------------------------------------------

@colander.deferred
def content_sequence_widget(node, kw):
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/content_sequence'
    )


class ModeField(colander.SchemaNode):
    oid = "mode"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    validator = colander.OneOf(['add', 'create', 'edit'])


class NameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


class CodeField(colander.SchemaNode):
    oid = "code"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    missing = ""


class CategoryField(colander.SchemaNode):
    oid = "category"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    missing = ""


# --- Schemas -----------------------------------------------------------------

class ContentSchema(colander.Schema):
    mode = ModeField()
    name = NameField()
    code = CodeField()
    code = CategoryField()
    title = ""


class ContentSequence(DatatableSequence):
    content_sequence = ContentSchema()
    widget = content_sequence_widget
