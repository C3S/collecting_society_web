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
from . import CreationSequence

log = logging.getLogger(__name__)


def prepare_ignored(value):
    # workaround for conditinally required fields, as form validators are not
    # processed, if a normal required field is missing
    return value if value else "IGNORED"


def prepare_required(value):
    # oid required for add/edit
    if value['mode'] != "create" and value['oid'] == "IGNORED":
        value['oid'] = ""
    return value


# --- Fields ------------------------------------------------------------------

@colander.deferred
def original_sequence_widget(node, kw):
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/original_sequence'
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


class TypeField(colander.SchemaNode):
    oid = "type"
    schema_type = colander.String
    widget = deform.widget.Select2Widget(values=(
        ('adaption', _('Adaption')),
        ('cover', _('Cover')),
        ('remix', _('Remix')),
    ))
    validator = colander.OneOf(
        ['adaption', 'cover', 'remix'])


# --- Schemas -----------------------------------------------------------------

class OriginalSchema(colander.Schema):
    oid = OidField()
    mode = ModeField()
    type = TypeField()
    original = CreationSequence(min_len=1, max_len=1)
    title = ""
    preparer = [prepare_required]


class OriginalSequence(DatatableSequence):
    original_sequence = OriginalSchema()
    widget = original_sequence_widget
    actions = ['create', 'edit']
