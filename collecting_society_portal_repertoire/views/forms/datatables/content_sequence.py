# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

import colander
import deform
from pyramid.i18n import get_localizer

from collecting_society_portal.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)

from ....services import _
from ....models import Content

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
def content_sequence_widget(node, kw):
    request = kw.get('request')
    # translation strings
    request.name_translation = get_localizer(
        request).translate(
            _(u'Name', 'collecting_society_portal_repertoire'))
    request.code_translation = get_localizer(
        request).translate(
            _(u'Code', 'collecting_society_portal_repertoire'))
    locale = get_localizer(request)
    locale_domain = 'collecting_society_portal_repertoire'
    content_category = {
        'audio': locale.translate(_(u'Audio', locale_domain)),
        'sheet': locale.translate(_(u'Sheet Music', locale_domain)),
        'lyrics': locale.translate(_(u'Lyrics', locale_domain)),
    }
    # get initial source data
    source_data = []
    domain = [
        ('entity_creator', '=', request.web_user.party.id),  # only own
        ('creation', '=', None)                              # only orphaned
    ]
    if getattr(node, 'category', None):
        domain.append(('category', '=', node.category))
    contents = Content.search(
        domain=domain,
        offset=0,
        limit=10,
        order=[('name', 'asc')])
    for content in contents:
        source_data.append({
            'oid': content.oid,
            'name': content.name,
            'code': content.code,
            'category': content_category[content.category]})
    # get statistics
    total_domain = [
        ('entity_creator', '=', request.web_user.party.id),  # only own
        ('creation', '=', None)                              # only orphaned
    ]
    if getattr(node, 'category', None):
        total_domain.append(('category', '=', node.category))
    total = Content.search_count(total_domain)
    # return widget
    return DatatableSequenceWidget(
        request=request,
        template='datatables/content_sequence',
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
        colander.Regex(r'^D\d{10}\Z'),
        colander.Regex(r'^IGNORED\Z', '')
    )


class CategoryField(colander.SchemaNode):
    oid = "category"
    schema_type = colander.String
    widget = deform.widget.HiddenWidget()


# --- Schemas -----------------------------------------------------------------


class ContentSchema(colander.Schema):
    mode = ModeField()
    oid = OidField()
    name = NameField()
    code = CodeField()
    preparer = [prepare_required]
    title = ""


class ContentSequence(DatatableSequence):
    content_sequence = ContentSchema()
    widget = content_sequence_widget
