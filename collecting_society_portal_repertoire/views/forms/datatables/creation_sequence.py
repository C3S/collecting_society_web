# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

import colander
import deform

from collecting_society_portal.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)

from ....services import _

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
def creation_sequence_widget(node, kw):
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/creation_sequence'
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


class TitleField(colander.SchemaNode):
    oid = "titlefield"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


class CodeField(colander.SchemaNode):
    oid = "code"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    preparer = [code_ignored]


class ArtistField(colander.SchemaNode):
    oid = "artist"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


# --- Schemas -----------------------------------------------------------------

class CreationSchema(colander.Schema):
    mode = ModeField()
    oid = OidField()
    titlefield = TitleField(title=_("Title"))
    artist = ArtistField()
    code = CodeField()
    title = ""
    preparer = [
        oid_required_conditionally,
        code_required_conditionally,
    ]


class CreationSequence(DatatableSequence):
    creation_sequence = CreationSchema()
    widget = creation_sequence_widget
