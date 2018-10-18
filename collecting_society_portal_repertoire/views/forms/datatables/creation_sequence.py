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


class TitleField(colander.SchemaNode):
    oid = "titlefield"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


class ArtistField(colander.SchemaNode):
    oid = "artist"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


class CodeField(colander.SchemaNode):
    oid = "code"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    missing = ""


# --- Schemas -----------------------------------------------------------------

class CreationSchema(colander.Schema):
    mode = ModeField()
    titlefield = TitleField()
    artist = ArtistField()
    code = CodeField()
    title = ""


class CreationSequence(DatatableSequence):
    creation_sequence = CreationSchema()
    widget = creation_sequence_widget
