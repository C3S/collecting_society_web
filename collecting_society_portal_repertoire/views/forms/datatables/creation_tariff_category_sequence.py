# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging

import colander
import deform

from collecting_society_portal.views.forms.datatables import (
    DatatableSequence,
    DatatableSequenceWidget
)

from ....models import (
    TariffCategory,
    CollectingSociety
)

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
def creation_tariff_category_sequence_widget(node, kw):
    return DatatableSequenceWidget(
        request=kw.get('request'),
        template='datatables/creation_tariff_category_sequence'
    )


@colander.deferred
def category_widget(node, kw):
    values = [(tc.oid, tc.name) for tc in TariffCategory.search_all()]
    return deform.widget.Select2Widget(values=values)


@colander.deferred
def collecting_society_widget(node, kw):
    values = [(tc.oid, tc.name) for tc in CollectingSociety.search(
        [("represents_copyright", "=", True)])]
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


class CategoryField(colander.SchemaNode):
    oid = "category"
    schema_type = colander.String
    widget = category_widget
    validator = colander.uuid


class CollectingSocietyField(colander.SchemaNode):
    oid = "collecting_society"
    schema_type = colander.String
    widget = collecting_society_widget
    validator = colander.uuid


# --- Schemas -----------------------------------------------------------------

class CreationTariffCategorySchema(colander.Schema):
    mode = ModeField()
    oid = OidField()
    category = CategoryField()
    collecting_society = CollectingSocietyField()
    preparer = [prepare_required]
    title = ""


class CreationTariffCategorySequence(DatatableSequence):
    creation_tariff_category_sequence = CreationTariffCategorySchema()
    widget = creation_tariff_category_sequence_widget
    actions = ['create', 'edit']

    def validator(self, sequence, value):
        previous = []
        duplicates = []
        for sequence_item in value:
            category_oid = sequence_item['category']
            if category_oid in previous:
                category = TariffCategory.search_by_oid(category_oid)
                if category.name not in duplicates:
                    duplicates.append(category.name)
            previous.append(category_oid)
        if duplicates:
            msg = "Multiple entries: {}".format(", ".join(duplicates))
            raise colander.Invalid(sequence, msg)
