# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

import colander
import deform

from portal_web.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)

from ....services import _
from ....models import Creation

log = logging.getLogger(__name__)


def prepare_ignored(value):
    # workaround for conditinally required fields, as form validators are not
    # processed, if a normal required field is missing
    return value if value else "IGNORED"


def prepare_required(value):
    # oid required for add/edit
    if value['mode'] != "create" and value['oid'] == "IGNORED":
        value['oid'] = ""
    # code required for add/edit
    if value['mode'] != "create" and value['code'] == "IGNORED":
        value['code'] = ""
    return value


# --- Fields ------------------------------------------------------------------

@colander.deferred
def creation_sequence_widget(node, kw):
    # get initial source data
    source_data = []
    domain = []
    creations = Creation.search(
        domain=domain,
        offset=0,
        limit=10,
        order=[('title', 'asc')])
    for creation in creations:
        source_data.append({
            'oid': creation.oid,
            'titlefield': creation.title,
            'artist': creation.artist.name,
            'code': creation.code})
    # get statistics
    total_domain = []
    total = Creation.search_count(total_domain)
    # return widget
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/creation_sequence',
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


class TitleField(colander.SchemaNode):
    oid = "titlefield"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


class CodeField(colander.SchemaNode):
    oid = "code"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    preparer = [prepare_ignored]
    validator = colander.Any(
        colander.Regex(r'^C\d{10}\Z'),
        colander.Regex(r'^IGNORED\Z', '')
    )


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
    preparer = [prepare_required]
    title = ""


class CreationSequence(DatatableSequence):
    creation_sequence = CreationSchema()
    widget = creation_sequence_widget
