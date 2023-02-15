# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

import colander
import deform

from portal_web.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)

from ....models import (
    License,
    Creation
)

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
def track_sequence_widget(node, kw):
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
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/track_sequence',
        item_template='datatables/track_sequence_item',
        source_data=source_data,
        source_data_total=total,
        language_overrides=getattr(node, "language_overrides", {})
    )


@colander.deferred
def deferred_license_widget(node, kw):
    values = [(x.oid, x.name) for x in License.search_all()]
    return deform.widget.Select2Widget(values=values)


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


class TrackTitleField(colander.SchemaNode):
    oid = "track_title"
    schema_type = colander.String
    widget = deform.widget.TextInputWidget()


# class MediumNumberField(colander.SchemaNode):
#     oid = "medium_number"
#     schema_type = colander.Integer
#     widget = deform.widget.TextInputWidget()


# class TrackNumberField(colander.SchemaNode):
#     oid = "track_number"
#     schema_type = colander.Integer
#     widget = deform.widget.TextInputWidget()


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
    preparer = [prepare_required]
    title = ""


class TrackSequence(DatatableSequence):
    # title = _(u"Tracks")
    track_sequence = TrackSchema()
    widget = track_sequence_widget
    actions = ['create', 'edit']
    orderable = 1
