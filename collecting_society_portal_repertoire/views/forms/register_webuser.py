# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import colander
import deform
import logging

from collecting_society_portal.views.forms import LoginWebuser
from collecting_society_portal.models import WebUser
from ...services import _

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class RegisterWebuser(LoginWebuser):
    """
    form controller for registration of web_user
    """

    __stage__ = 'has_membership'  # initial stage

    def controller(self):

        if self.stage == 'has_membership':
            self.has_membership()

        if self.stage == 'wants_membership':
            self.wants_membership()

        if self.stage == 'register_webuser':
            self.register_webuser()

        return self.response

    # --- Stages --------------------------------------------------------------

    def has_membership(self):
        self.form = has_membership_form(self.request)
        self.render(self.data)

        # has membership
        if self.submitted('has_membership'):
            self.data.update({'member': 1})
            self.stage = 'register_webuser'
            self.register_webuser()

        # has no membership
        if self.submitted('has_no_membership'):
            self.data.update({'member': 0})
            self.stage = 'wants_membership'
            self.wants_membership()

    def wants_membership(self):
        self.form = wants_membership_form(self.request)
        self.render(self.data)

        # wants membership
        if self.submitted('wants_membership'):
            self.redirect("https://yes.c3s.cc?from=repertoire")

        # wants no membership
        if self.submitted('wants_no_membership'):
            self.stage = 'register_webuser'
            self.register_webuser()

        # back
        if self.submitted('back'):
            self.stage = 'has_membership'
            self.has_membership()

    def register_webuser(self):
        if self.data['member']:
            self.form = register_member_form(self.request)
        else:
            self.form = register_nonmember_form(self.request)

        # register webuser
        if self.submitted('register_webuser') and self.validate():
            self.register()
            # self.login()

        # back
        if self.submitted('back'):
            if self.data['member']:
                self.stage = 'has_membership'
                self.has_membership()
            else:
                self.stage = 'wants_membership'
                self.wants_membership()

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def register(self):
        web_user = {
            'email': self.appstruct['email'],
            'password': self.appstruct['password']
        }
        # WebUser.create([web_user])
        log.info("web_user creation successful: %s" % self.appstruct['email'])


# --- Validators --------------------------------------------------------------

def email_is_unique(value):
    if not WebUser.search_by_email(value):
        return True
    return _(u'Email already registered')


# --- Options -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

class EmailField(colander.SchemaNode):
    oid = "email"
    schema_type = colander.String
    validator = colander.All(
        colander.Email(),
        colander.Function(email_is_unique)
    )


class CheckedPasswordField(colander.SchemaNode):
    oid = "password"
    schema_type = colander.String
    validator = colander.Length(min=8)
    widget = deform.widget.CheckedPasswordWidget()


# --- Schemas -----------------------------------------------------------------

class RegisterMemberSchema(colander.MappingSchema):
    email = EmailField(
        title=_(u"Email"),
        description=_(
            u"Please use the email address as in your membership application."
        )
    )
    password = CheckedPasswordField(
        title=_(u"Password")
    )


class RegisterNonmemberSchema(colander.MappingSchema):
    email = EmailField(
        title=_(u"Email")
    )
    password = CheckedPasswordField(
        title=_(u"Password")
    )


# --- Forms -------------------------------------------------------------------

def has_membership_form(request):
    return deform.Form(
        title=_(u"Are you a C3S member?"),
        schema=colander.MappingSchema(),
        action=request.path,
        buttons=[
            deform.Button(
                'has_membership', _(u"Yes"), css_class="btn-default btn-lg"
            ),
            deform.Button('has_no_membership', _(u"No"))
        ]
    )


def wants_membership_form(request):
    return deform.Form(
        title=_(u"Do you want to apply for C3S membership?"),
        schema=colander.MappingSchema(),
        action=request.path,
        buttons=[
            deform.Button('wants_membership', _(u"Yes"), css_class="btn-lg"),
            deform.Button('wants_no_membership', _(u"No")),
            deform.Button('back', _(u"Back"), css_class="btn-xs")
        ]
    )


def register_member_form(request):
    return deform.Form(
        schema=RegisterMemberSchema(),
        action=request.path,
        buttons=[
            deform.Button(
                'register_webuser', _(u"Register"), css_class="btn-lg"
            ),
            deform.Button('back', _(u"Back"))
        ]
    )


def register_nonmember_form(request):
    return deform.Form(
        schema=RegisterNonmemberSchema(),
        action=request.path,
        buttons=[
            deform.Button(
                'register_webuser', _(u"Register"), css_class="btn-lg"
            ),
            deform.Button('back', _(u"Back"))
        ]
    )
