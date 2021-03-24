# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import colander
import deform

from portal_web.models import Tdb
from portal_web.views.forms import FormController

from ...services import _
from ...models import Declaration

log = logging.getLogger(__name__)


class AddDeclaration(FormController):
    """
    form controller for creation of declarations
    """

    def controller(self):
        self.form = add_declaration_form(self.request)
        self.render()
        if self.submitted():
            if self.validate():
                self.create_declaration()
        else:
            self.init_declaration()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def init_declaration(self):
        """
        initializes form with arguments passed via url from Content/Uploads
        """

        if not self.appstruct:
            self.appstruct = {
                'general': {
                    'template': '',
                    # 'period': '',
                }
            }

        # render form with init data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def create_declaration(self):
        web_user = self.request.web_user

        # generate vlist
        _declaration = {
            'template': self.appstruct['general']['template'],
            # 'period': self.appstruct['general']['period']
        }

        # remove empty fields
        for index, value in _declaration.items():
            if not value:
                del _declaration[index]

        # create declaration
        declaration = Declaration.create([_declaration])

        # user feedback
        if not declaration:
            log.info("declaration add failed for %s: %s" % (
                web_user, _declaration))
            # self.request.session.flash(
            #     _(u"Declaration could not be added: ${period}",
            #       mapping={'period': _declaration['period']}),
            #     'main-alert-danger'
            # )
            self.redirect()
            return
        declaration = declaration[0]
        log.info("declaration add successful for %s: %s" % (
            web_user, declaration))
        # self.request.session.flash(
        #     _(u"Declaration '${period}' added to your account. "
        #       "Your declaration token is ${template}.",
        #       mapping={'period': declaration.period,
        #                'template': str(declaration.template)}),
        #     'main-alert-success'
        # )

        # redirect
        self.redirect()


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Widgets -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------


# -- General tab --

class TemplateField(colander.SchemaNode):
    oid = "template"
    schema_type = colander.Boolean


# --- Schemas -----------------------------------------------------------------

class GeneralSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    template = TemplateField(title=_(u"Template"))


class AddDeclarationSchema(colander.Schema):
    widget = deform.widget.FormWidget(template='navs/form', navstyle='tabs')
    general = GeneralSchema(title=_(u"General"))


# --- Forms -------------------------------------------------------------------

def add_declaration_form(request):
    return deform.Form(
        schema=AddDeclarationSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
