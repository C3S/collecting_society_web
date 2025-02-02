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
from .forms import (
    AddDeclarationLive,
    ConfirmDeclarationLive,
    FinalizeDeclarationLive,
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
        name='confirm',
        renderer='../templates/declaration/confirm.pt',
        permission='confirm_declaration')
    def confirm(self):
        declaration = self.context.declaration

        # check declaration state
        if declaration.next_step != 'confirmation':
            log.warning("declaration confirm with wrong state: "
                        "declaration '%s', next_step '%s', web user '%s'" % (
                            declaration,
                            declaration.next_step,
                            self.request.web_user))
            self.request.session.flash(
                _("Declaration could not be confirmed: ${declaration}",
                  mapping={'declaration': declaration.context.name}),
                'main-alert-danger'
            )
            return self.redirect()

        # choose tariff form
        form = False
        if declaration.tariff.category.code == 'L':
            form = ConfirmDeclarationLive
        # TODO: implement other tariffs
        if not form:
            return {'ConfirmDeclaration': ''}

        # process
        self.register_form(form, name="ConfirmDeclaration")
        return self.process_forms()

    @view_config(
        name='finalize',
        renderer='../templates/declaration/finalize.pt',
        permission='finalize_declaration')
    def finalize(self):
        declaration = self.context.declaration

        # check declaration state
        if declaration.next_step != 'finalization':
            log.warning("declaration finalize with wrong state: "
                        "declaration '%s', next_step '%s', web user '%s'" % (
                            declaration,
                            declaration.next_step,
                            self.request.web_user))
            self.request.session.flash(
                _("Declaration could not be finalized: ${declaration}",
                  mapping={'declaration': declaration.context.name}),
                'main-alert-danger'
            )
            return self.redirect()

        # choose tariff form
        form = False
        if declaration.tariff.category.code == 'L':
            form = FinalizeDeclarationLive
        # TODO: implement other tariffs
        if not form:
            return {'FinalizeDeclaration': ''}

        # process
        self.register_form(form, name="FinalizeDeclaration")
        return self.process_forms()

    @view_config(
        name='cancel',
        decorator=Tdb.transaction(readonly=False),
        permission='cancel_declaration')
    def cancel(self):
        web_user = self.request.web_user
        declaration = self.context.declaration

        # check declaration state
        cancelable_next_steps = ['utilisation', 'estimation', 'confirmation']
        if declaration.next_step not in cancelable_next_steps:
            log.warning("declaration cancel with wrong state: "
                        "declaration '%s', next_step '%s', web user '%s'" % (
                            declaration,
                            declaration.next_step,
                            self.request.web_user))
            self.request.session.flash(
                _("Declaration could not be canceled: ${declaration}",
                  mapping={'declaration': declaration.context.name}),
                'main-alert-danger'
            )
            return self.redirect()

        # process
        declaration.state = 'canceled'
        declaration.save()

        # user feedback
        log.info("declaration cancel successful for %s: %s" % (
            web_user, declaration
        ))
        self.request.session.flash(
            _("Declaration canceled: ${declaration}",
              mapping={'declaration': declaration.context.name}),
            'main-alert-success'
        )
        return self.redirect('..')
