# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

import colander
import deform

from collecting_society_portal.views.forms.datatables import (
    DatatableSequenceWidget
)

log = logging.getLogger(__name__)


def email_ignored(value):
    return value if value else "IGNORE@DUMMY.EMAIL"


def email_required_conditionally(value):
    if value['mode'] != "add" and value['email'] == "IGNORE@DUMMY.EMAIL":
        value['email'] = ""
    return value


# --- Fields ------------------------------------------------------------------

@colander.deferred
def artist_sequence_widget(node, kw):
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/artist_sequence'
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


class DescriptionField(colander.SchemaNode):
    oid = "description"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    missing = ""


class EmailField(colander.SchemaNode):
    oid = "email"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()
    validator = colander.Email()
    preparer = [email_ignored]


# --- Schemas -----------------------------------------------------------------

class ArtistSchema(colander.Schema):
    mode = ModeField()
    name = NameField()
    description = DescriptionField()
    code = CodeField()
    email = EmailField()
    title = ""
    preparer = [email_required_conditionally]


class ArtistSequence(colander.SequenceSchema):
    artist = ArtistSchema()
    widget = artist_sequence_widget
