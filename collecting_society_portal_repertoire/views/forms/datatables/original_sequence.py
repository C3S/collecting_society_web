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
from . import CreationSequence

log = logging.getLogger(__name__)


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
    validator = colander.OneOf(['add', 'create', 'edit'])


class CodeField(colander.SchemaNode):
    oid = "code"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    missing = ""


class TypeField(colander.SchemaNode):
    oid = "type"
    schema_type = colander.String
    widget = deform.widget.Select2Widget(values=(
        ('adaption', _('Adaption')),
        ('cover', _('Cover')),
        ('remix', _('Remix')),
    ))
    missing = ""


# --- Schemas -----------------------------------------------------------------

class OriginalSchema(colander.Schema):
    mode = ModeField()
    type = TypeField()
    original = CreationSequence(min_len=1, max_len=1)
    title = ""


class OriginalSequence(DatatableSequence):
    original_sequence = OriginalSchema()
    widget = original_sequence_widget
    actions = ['create', 'edit']
