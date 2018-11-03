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
from ....models import License
from . import CreationSequence

log = logging.getLogger(__name__)

dummy_uuid = "4bbac9bf-5006-4c63-8f09-20b1c3303395"


def oid_ignored(value):
    return value if value else dummy_uuid


def oid_required_conditionally(value):
    if value['mode'] == "edit" and value['oid'] == dummy_uuid:
        value['oid'] = ""
    return value


# --- Fields ------------------------------------------------------------------

@colander.deferred
def track_sequence_widget(node, kw):
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/track_sequence',
        item_template='datatables/track_sequence_item'
    )


@colander.deferred
def deferred_license_widget(node, kw):
    values = [(l.oid, l.name) for l in License.search_all()]
    return deform.widget.Select2Widget(values=values)


class OidField(colander.SchemaNode):
    oid = "oid"
    schema_type = colander.String
    validator = colander.uuid
    widget = deform.widget.HiddenWidget()
    preparer = [oid_ignored]


class ModeField(colander.SchemaNode):
    oid = "mode"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()
    validator = colander.OneOf(['add', 'create', 'edit'])


class TrackTitleField(colander.SchemaNode):
    oid = "track_title"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


class MediumNumberField(colander.SchemaNode):
    oid = "medium_number"
    schema_type = colander.Integer
    widget = deform.widget.TextInputWidget()


class TrackNumberField(colander.SchemaNode):
    oid = "track_number"
    schema_type = colander.Integer
    widget = deform.widget.TextInputWidget()


class LicenseField(colander.SchemaNode):
    oid = "license"
    schema_type = colander.String
    validator = colander.uuid
    widget = deferred_license_widget


# --- Schemas -----------------------------------------------------------------

class TrackSchema(colander.Schema):
    oid = OidField()
    mode = ModeField()
    track = CreationSequence(min_len=1, max_len=1)
    track_title = TrackTitleField()
    license = LicenseField()
    # medium_number = MediumNumberField()
    # track_number = TrackNumberField()
    title = ""
    preparer = [oid_required_conditionally]


class TrackSequence(DatatableSequence):
    track_sequence = TrackSchema()
    widget = track_sequence_widget
    actions = ['create', 'edit']
    orderable = 1
