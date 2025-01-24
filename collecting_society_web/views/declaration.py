# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging

from pyramid.renderers import get_renderer
from pyramid.view import (
    view_config,
    view_defaults
)

from portal_web.models import Tdb
from portal_web.views import ViewBase

from ..services import _
from ..models import Declaration
from .forms import (
    AddDeclarationLive,
    EditDeclaration
)

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.DeclarationsResource')
class DeclarationsViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/declaration/list.pt',
        permission='list_declarations')
    def list(self):
        return {}


@view_defaults(
    context='..resources.AddDeclarationResource',
    permission='add_declarations')
class AddDeclarationViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/declaration/add/choose_tariff_category.pt')
    def choose_tariff_category(self):
        return {}

    @view_config(
        name='L',
        renderer='../templates/declaration/add/add_declaration_live.pt')
    def create_tariff__L(self):
        self.register_form(AddDeclarationLive)
        return self.process_forms()


@view_defaults(
    context='..resources.DeclarationResource')
class DeclarationViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/declaration/show.pt',
        permission='view_declaration')
    def show(self):
        template = get_renderer(
            '../templates/declaration/show-macros.pt').implementation()
        return {'macros': template.macros}

    @view_config(
        name='edit',
        renderer='../templates/declaration/edit.pt',
        permission='edit_declaration')
    def edit(self):
        self.register_form(EditDeclaration)
        return self.process_forms()

    @view_config(
        name='delete',
        permission='delete_declaration',
        decorator=Tdb.transaction(readonly=False))
    def delete(self):
        name = self.context.declaration.name
        Declaration.delete([self.context.declaration])
        log.info("declaration delete successful for %s: %s (%s)" % (
            self.request.web_user, name, self.context.code
        ))
        self.request.session.flash(
            _("Declaration deleted: ") + name + ' (' + self.context.id + ')',
            _("Declaration deleted: ${name} (${id})",
              mapping={'name': name, 'id': self.context.id}),
            'main-alert-success'
        )
        return self.redirect('..')
