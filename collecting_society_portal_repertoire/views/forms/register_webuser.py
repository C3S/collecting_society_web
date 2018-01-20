# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import colander
import deform
import logging
import datetime

from collecting_society_portal.resources import FrontendResource
from collecting_society_portal.views.forms import LoginWebuser
from collecting_society_portal.models import (
    Tdb,
    WebUser
)
from collecting_society_portal.services import send_mail

from ...services import _

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class RegisterWebuser(LoginWebuser):
    """
    form controller for registration of web_user
    """

    __stage__ = 'claims_membership'  # initial stage

    def controller(self):

        if self.stage == 'claims_membership':
            self.claims_membership()

        if self.stage == 'wants_membership':
            self.wants_membership()

        if self.stage == 'register_webuser':
            self.register_webuser()

        return self.response

    # --- Stages --------------------------------------------------------------

    def claims_membership(self):
        self.stage = 'claims_membership'
        self.form = claims_membership_form()
        self.render(self.data)

        # has membership
        if self.submitted('claims_membership'):
            self.data.update({'member_c3s': True})
            self.register_webuser()

        # has no membership
        if self.submitted('claims_no_membership'):
            self.data.update({'member_c3s': False})
            self.wants_membership()

    def wants_membership(self):
        self.stage = 'wants_membership'
        self.form = wants_membership_form()
        self.render(self.data)

        # wants membership
        if self.submitted('wants_membership'):
            self.redirect("https://yes.c3s.cc?from=repertoire")

        # wants no membership
        if self.submitted('wants_no_membership'):
            self.register_webuser()

        # back
        if self.submitted('back'):
            self.claims_membership()

    def register_webuser(self):
        self.stage = 'register_webuser'
        if self.data['member_c3s']:
            # TODO: Change back, when membership is integrated
            # self.form = register_member_form()
            self.form = register_nonmember_form()
        else:
            self.form = register_nonmember_form()

        # register webuser
        if self.submitted('register_webuser') and self.validate():
            self.data.update(self.appstruct.copy())
            self.register()

        # back
        if self.submitted('back'):
            if self.data['member_c3s']:
                self.claims_membership()
            else:
                self.wants_membership()

    # --- Conditions ----------------------------------------------------------

    def is_registered(self, web_user):
        if WebUser.search_by_email(web_user['email']):
            return True
        return False

    def passes_authentication(self, web_user):
        if WebUser.authenticate(web_user['email'], web_user['password']):
            return True
        return False

    def is_claiming_membership(self, data):
        if data['member_c3s']:
            return True
        return False

    def is_member(self, api, web_user):
        # TODO: Change back, when membership is integrated
        # return api.is_member(
        #     service='repertoire',
        #     email=web_user['email']
        # )
        return False

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=False)
    def register(self):
        _create = False
        _web_user = {
            'email': self.data['email'],
            'password': self.data['password']
        }
        _c3smembership = self.context.registry['services']['c3smembership']
        template_variables = {}

        # user is already registered
        if self.is_registered(_web_user):
            # user passes authentication (accidently registered to login)
            if self.passes_authentication(_web_user):
                opt_in_state = WebUser.get_opt_in_state_by_email(
                    _web_user['email']
                )
                if opt_in_state == 'opted-in':
                    self.request.session.flash(
                        _(u"You are already registered with your credentials."),
                        'main-alert-info'
                    )
                    self.login()
                    return
                else:
                    self.request.session.flash(
                        _(
                            u"Your email address is not verified yet. Please "
                            u"follow the instructions in our email."
                        ),
                        'main-alert-info'
                    )
                    return
            # user fails authentication (email already registered)
            else:
                template_name = "registration-fail_registered"
        # user is not registered yet
        else:
            # user claims to be a c3s member
            if self.is_claiming_membership(self.data):
                # TODO: Change back, when membership is integrated
                # # user is a c3s member
                # if self.is_member(_c3smembership, _web_user):
                #     _create = True
                #     template_name = "registration-member_success"
                # # user is not a c3s member
                # else:
                #     template_name = "registration-member_fail_nomatch"
                _create = True
                template_name = "registration-member_success"
            # user claims not to be a c3s member
            else:
                # TODO: Change back, when membership is integrated
                # # user is a c3s member
                # if self.is_member(_c3smembership, _web_user):
                #     template_name = "registration-nonmember_fail_reserved"
                # # user is not a c3s member
                # else:
                #     _create = True
                #     template_name = "registration-nonmember_success"
                _create = True
                template_name = "registration-nonmember_success"

        # create
        if _create:
            web_users = WebUser.create([_web_user])

            # creation failed
            if not web_users or len(web_users) is not 1:
                log.info("web_user creation not successful: %s" % _web_user)
                self.request.session.flash(
                    _(
                        u"There was an error during the registration process. "
                        u"Please try again later and contact us, if this "
                        u"error occurs again. Sorry for the inconveniece."
                    ),
                    'main-alert-danger'
                )
                return False

            # creation successful
            web_user = web_users[0]
            if self.is_member(_c3smembership, _web_user):
                # c3s membership
                web_user.party.member_c3s = True
                response = _c3smembership.generate_member_token(
                    service='repertoire',
                    email=web_user.email
                )
                if not response or 'token' not in response:
                    log.debug(
                        "web_user c3s membership token error: %s, %s" % (
                            _web_user, response
                        )
                    )
                web_user.party.member_c3s_token = response['token']
                web_user.party.save()
            else:
                # save values of non-c3s-member form fields
                web_user.party.repertoire_terms_accepted = self.data['terms_accepted']
                web_user.party.name = self.data['firstname'] + ' ' + self.data['lastname']
                web_user.party.firstname = self.data['firstname']   # also save separately for clarity
                web_user.party.lastname =  self.data['lastname']
                web_user.party.birthdate = self.data['birthdate']
                web_user.party.save()

            template_variables = {
                'link': self.request.resource_url(
                    self.request.root, 'verify_email',
                    WebUser.get_opt_in_uuid_by_id(web_user.id)
                )
            }
            log.info("web_user creation successful: %s" % web_user.email)

        # flash message
        self.request.session.flash(
            _(
                u"Thank you for your registration. We are now processing your "
                u"request and will send you an email with further "
                u"instructions."
            ),
            'main-alert-success'
        )

        # send mail
        send_mail(
            self.request,
            template=template_name,
            variables=template_variables,
            recipients=[_web_user['email']]
        )
        web_user.opt_in_state = "mail-sent"
        web_user.save()

        # reset form
        self.redirect(FrontendResource)


# --- Validators --------------------------------------------------------------


def not_empty(value):
    if not value or len(str(value)) < 2:
        return _(u"Please enter your name.")
    return True

def terms_accepted(value):
    if not value:
        return _(u"You need to accept the terms of service.")
    return True


# --- Options -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

class FirstnameField(colander.SchemaNode):
    oid = "firstname"
    schema_type = colander.String
    validator = colander.Function(not_empty)


class LastnameField(colander.SchemaNode):
    oid = "lastname"
    schema_type = colander.String
    validator = colander.Function(not_empty)

AGE_ADULT = 16 # don't allow kids
class BirthdateField(colander.SchemaNode):
    oid = "birthdate"
    schema_type = colander.Date
    validator = colander.Range(
                    max=datetime.date.today() - datetime.timedelta(days=AGE_ADULT*364),
                    max_err=_('Sorry, you have to be ' + str(AGE_ADULT) +' years or older to register here.')
                )


class EmailField(colander.SchemaNode):
    oid = "register_email"
    schema_type = colander.String
    validator = colander.Email()


class CheckedPasswordField(colander.SchemaNode):
    oid = "register_password"
    schema_type = colander.String
    validator = colander.Length(min=8)
    widget = deform.widget.CheckedPasswordWidget()


class CheckboxWithLabel(colander.SchemaNode):
    oid = "terms_accepted"
    schema_type = colander.Boolean
    validator = colander.Function(terms_accepted)


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
    terms_accepted = CheckboxWithLabel(
        title=_(u"Terms of Service"),
        label=_(u"I accept the terms of service.")
    )


class RegisterNonmemberSchema(colander.MappingSchema):
    firstname = FirstnameField(
        title=_(u"Firstname")
    )
    lastname = LastnameField(
        title=_(u"Lastname")
    )
    birthdate = BirthdateField(
        title=_(u"Birthdate")
    )
    email = EmailField(
        title=_(u"Email")
    )
    password = CheckedPasswordField(
        title=_(u"Password")
    )
    terms_accepted = CheckboxWithLabel(
        title=_(u"Terms of Service"),
        label=_(u"I accept the terms of service.")
    )


# --- Forms -------------------------------------------------------------------

def claims_membership_form():
    return deform.Form(
        title=_(u"Are you a C3S member?"),
        schema=colander.MappingSchema(),
        buttons=[
            deform.Button(
                'claims_membership', _(u"Yes"), css_class="btn-default btn-lg"
            ),
            deform.Button('claims_no_membership', _(u"No"))
        ]
    )


def wants_membership_form():
    return deform.Form(
        title=_(u"Do you want to apply for C3S membership?"),
        schema=colander.MappingSchema(),
        buttons=[
            deform.Button('wants_membership', _(u"Yes"), css_class="btn-lg"),
            deform.Button('wants_no_membership', _(u"No")),
            deform.Button('back', _(u"Back"), css_class="btn-xs")
        ]
    )


def register_member_form():
    return deform.Form(
        schema=RegisterMemberSchema(),
        buttons=[
            deform.Button(
                'register_webuser', _(u"Register"), css_class="btn-lg"
            ),
            deform.Button('back', _(u"Back"))
        ]
    )


def register_nonmember_form():
    return deform.Form(
        schema=RegisterNonmemberSchema(),
        buttons=[
            deform.Button(
                'register_webuser', _(u"Register"), css_class="btn-lg"
            ),
            deform.Button('back', _(u"Back"))
        ]
    )
