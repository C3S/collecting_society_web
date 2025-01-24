# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import colander
import deform

from portal_web.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)

from . import ArtistSequence


def prepare_ignored(value):
    # workaround for conditinally required fields, as form validators are not
    # processed, if a normal required field is missing
    return value if value else "IGNORED"


def prepare_required(value):
    # oid required for add/edit
    if value['mode'] != "create" and value['oid'] == "IGNORED":
        value['oid'] = ""
    return value


# --- Widgets -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

@colander.deferred
def performance_sequence_widget(node, kw):
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/performance_sequence',
    )


class ModeField(colander.SchemaNode):
    oid = "mode"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    validator = colander.OneOf(
        ['create', 'edit'])


class OidField(colander.SchemaNode):
    oid = "oid"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    preparer = [prepare_ignored]
    validator = colander.Any(
        colander.uuid,
        colander.Regex(r'^IGNORED\Z', '')
    )


class StartField(colander.SchemaNode):
    oid = "start"
    schema_type = colander.DateTime


class EndField(colander.SchemaNode):
    oid = "end"
    schema_type = colander.DateTime


# --- Schemas -----------------------------------------------------------------

class PerformanceSchema(colander.Schema):
    mode = ModeField()
    oid = OidField()
    start = StartField()
    end = EndField()
    artist = ArtistSequence(min_len=1, max_len=1)
    preparer = [prepare_required]
    title = ""


class PerformanceSequence(DatatableSequence):
    performance_sequence = PerformanceSchema()
    widget = performance_sequence_widget
    actions = ['create', 'edit']
