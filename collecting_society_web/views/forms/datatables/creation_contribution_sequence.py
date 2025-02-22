# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

import colander
import deform

from portal_web.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)

from . import RightsholderIndividual, CreationRightSequence
from ....services import _

log = logging.getLogger(__name__)


# --- Options -----------------------------------------------------------------


# --- Fields ------------------------------------------------------------------

@colander.deferred
def creation_contribution_sequence_widget(node, kw):
    request = kw.get('request')
    # return widget
    return DatatableSequenceWidget(
        request=request,
        template='datatables/creation_contribution_sequence',
    )


class ModeField(colander.SchemaNode):
    oid = "mode"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    validator = colander.OneOf(
        ['create', 'edit'])


# --- Schemas -----------------------------------------------------------------


class CreationContributionSchema(colander.Schema):
    mode = ModeField()
    rightsholder = RightsholderIndividual(title=_("Rightsholder"))
    rights = CreationRightSequence(min_len=1)
    title = ""


class CreationContributionSequence(DatatableSequence):
    creation_contribution_sequence = CreationContributionSchema()
    widget = creation_contribution_sequence_widget
    actions = ['create', 'edit']
