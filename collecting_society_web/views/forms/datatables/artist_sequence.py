# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

import colander
import deform

from portal_web.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)

from ....models import Artist

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
    # email required for create/edit
    if value['mode'] != "add" and value['email'] == "IGNORED":
        value['email'] = ""
    return value


# --- Fields ------------------------------------------------------------------

@colander.deferred
def artist_sequence_widget(node, kw):
    # get initial source data
    source_data = []
    domain = []
    if getattr(node, 'group', None):
        domain.append(('group', '=', node.group))
    artists = Artist.search(
        domain=domain,
        offset=0,
        limit=10,
        order=[('name', 'asc')])
    for artist in artists:
        source_data.append({
            'name': artist.name,
            'code': artist.code,
            'oid': artist.oid,
            'description': artist.description})
    # get statistics
    total_domain = []
    if getattr(node, 'group', None):
        total_domain.append(('group', '=', node.group))
    total = Artist.search_count(total_domain)
    # return widget
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/artist_sequence',
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


class NameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


class CodeField(colander.SchemaNode):
    oid = "code"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    preparer = [prepare_ignored]
    validator = colander.Any(
        colander.Regex(r'^A\d{10}\Z'),
        colander.Regex(r'^IGNORED\Z', '')
    )


class DescriptionField(colander.SchemaNode):
    oid = "description"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    missing = ""


class EmailField(colander.SchemaNode):
    oid = "email"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()
    preparer = [prepare_ignored]
    validator = colander.Any(
        colander.Email(),
        colander.Regex(r'^IGNORED\Z', '')
    )


# --- Schemas -----------------------------------------------------------------

class ArtistSchema(colander.Schema):
    mode = ModeField()
    oid = OidField()
    name = NameField()
    description = DescriptionField()
    code = CodeField()
    email = EmailField()
    preparer = [prepare_required]
    title = ""


class ArtistSequence(DatatableSequence):
    artist_sequence = ArtistSchema()
    widget = artist_sequence_widget


class ArtistIndividual(ArtistSequence):
    min_len = 1
    max_len = 1
