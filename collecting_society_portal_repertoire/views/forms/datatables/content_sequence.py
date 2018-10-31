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


def oid_ignored(value):
    return value if value else "OIDIGNORED"


def code_ignored(value):
    return value if value else "CODEIGNORED"


def oid_required_conditionally(value):
    if value['mode'] != "add" and value['oid'] == "OIDIGNORED":
        value['oid'] = ""
    return value


def code_required_conditionally(value):
    if value['mode'] == "add" and value['code'] == "CODEIGNORED":
        value['code'] = ""
    return value


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


class OidField(colander.SchemaNode):
    oid = "oid"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    preparer = [oid_ignored]


class NameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


class CodeField(colander.SchemaNode):
    oid = "code"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    preparer = [code_ignored]


class CategoryField(colander.SchemaNode):
    oid = "category"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()


# --- Schemas -----------------------------------------------------------------

class ContentSchema(colander.Schema):
    mode = ModeField()
    oid = OidField()
    name = NameField()
    code = CodeField()
    category = CategoryField()
    title = ""
    preparer = [
        oid_required_conditionally,
        code_required_conditionally,
    ]


class ContentSequence(DatatableSequence):
    content_sequence = ContentSchema()
    widget = content_sequence_widget
