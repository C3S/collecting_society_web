# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import re
import colander
import deform
import uuid

from portal_web.models import Tdb, WebUser, Address, Country
from portal_web.views.forms import FormController
from portal_web.services import send_mail
from ...services import _

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class EditProfile(FormController):
    """
    form controller for editing the user profile
    """

    def controller(self):
        self.form = edit_profile_form(self.request)
        if self.submitted():
            if self.validate():
                self.edit_profile()
        else:
            self.load_declaration()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def load_declaration(self):
        # shortcuts
        web_user = self.request.web_user
        party = web_user.party
        address = party.addresses and party.addresses[0] or False

        # set appstruct
        self.appstruct = {
            'name': web_user.party.name or "",
            'firstname': web_user.party.firstname or "",
            'lastname': web_user.party.lastname or "",
            'email': web_user.email or "",
            'default_role': web_user.default_role,
        }
        if address:
            self.appstruct.update({
                'street': address.street,
                'postal_code': address.postal_code,
                'city': address.city,
                'country': address.country.code,
            })

        # render form with data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def edit_profile(self):
        # shortcuts: objects
        web_user = self.request.web_user
        email = web_user.email.lower()
        party = web_user.party
        address = party.addresses and party.addresses[0]
        country = Country.search_by_code(self.appstruct['country'])

        # shortcuts: appstruct
        _email = self.appstruct['email'].lower()
        _password = self.appstruct['password']

        # party
        party.firstname = self.appstruct['firstname']
        party.lastname = self.appstruct['lastname']
        party.name = f"{party.firstname} {party.lastname}"
        party.save()

        # address: edit
        if address:
            address.street = self.appstruct['street']
            address.postal_code = self.appstruct['postal_code']
            address.city = self.appstruct['city']
            address.country = country
            address.save()

        # address: create
        else:
            address_vlist = {
                'party': party,
                'street': self.appstruct['street'],
                'postal_code': self.appstruct['postal_code'],
                'city': self.appstruct['city'],
                'country': country,
            }
            Address.create([address_vlist])

        # web user
        web_user.default_role = self.appstruct['default_role']
        web_user.save()

        # web user: email
        email_has_changed = (_email != email)
        if email_has_changed:
            web_user.new_email = _email
            web_user.opt_in_uuid = str(uuid.uuid4())
            web_user.save()

            # email verification
            template_variables = {
                'old_email': email,
                'new_email': _email,
                'link': self.request.resource_url(
                    self.request.root, 'verify_email',
                    WebUser.get_opt_in_uuid_by_id(web_user.id)
                )
            }
            send_mail(
                self.request,
                template="new_email_verification",
                variables=template_variables,
                recipients=[web_user.new_email]
            )

        # web user: password
        if _password:
            web_user.password = _password
            web_user.save()

        # user feedback
        if email_has_changed:
            log.info(
                "edit profile add successful for %s, activation email sent."
                % (party.name))
            self.request.session.flash(
                _("Profile changed for: ${name}"
                  " -- activation email for new email address sent."
                  " Please check your (new) email inbox.",
                  mapping={'name': party.name}),
                'main-alert-success'
            )
        else:
            log.info(
                "edit profile add successful for %s"
                % (party.name))
            self.request.session.flash(
                _("Profile changed for: ${name}",
                  mapping={'name': party.name}),
                'main-alert-success'
            )

        self.redirect()


# --- Validators --------------------------------------------------------------

def not_empty(value):
    """Ensure field has at least two characters in it."""
    if not value or len(value) < 2:
        return _("Please enter your name.")
    return True


def validate_unique_user_email(node, values, **kwargs):  # multifield validator
    """Check for valid email and prevent duplicate usernames."""

    request = node.bindings["request"]
    email_value = values["email"]
    current_web_user = WebUser.current_web_user(request)
    if email_value != current_web_user.email:
        # email has been changed: check if it conflicts with other webuser
        found_conflicting_web_user = WebUser.search_by_email(email_value)
        if found_conflicting_web_user:
            raise colander.Invalid(node, _("Email address already taken"))

    # finally, check email format
    if len(email_value) > 7:
        pattern = '^[_a-zA-Z0-9-]+(\\.[_a-zA-Z0-9-]+)*@[a-zA-Z0-9-]+' + \
            '(\\.[a-zA-Z0-9-]+)*(\\.[a-zA-Z]{2,9})$'
        if re.match(pattern, email_value) is not None:
            return
    raise colander.Invalid(node, "Invalid email address")


# --- Options -----------------------------------------------------------------

default_role_options = [
    ('licenser', _('Licenser')),
    ('licensee', _('Licensee')),
]


# --- Widgets -----------------------------------------------------------------

@colander.deferred
def deferred_country_select_widget(node, kw):
    countries = Country.search_all()
    country_options = [(None, "")]
    country_options += [(country.code, country.name) for country in countries]
    widget = deform.widget.SelectWidget(values=country_options)
    return widget


# --- Fields ------------------------------------------------------------------

class FirstnameField(colander.SchemaNode):
    oid = "firstname"
    schema_type = colander.String
    validator = colander.Function(not_empty)


class LastnameField(colander.SchemaNode):
    oid = "lastname"
    schema_type = colander.String
    validator = colander.Function(not_empty)


class EmailField(colander.SchemaNode):
    oid = "email"
    schema_type = colander.String


class PasswordField(colander.MappingSchema):
    oid = "password"
    schema_type = colander.String
    validator = colander.Length(min=8)
    widget = deform.widget.CheckedPasswordWidget()
    missing = ''


class StreetField(colander.SchemaNode):
    oid = "street"
    schema_type = colander.String


class PostalCodeField(colander.SchemaNode):
    oid = "postal_code"
    schema_type = colander.String


class CityField(colander.SchemaNode):
    oid = "city"
    schema_type = colander.String


class CountryField(colander.SchemaNode):
    oid = "country"
    schema_type = colander.String
    widget = deferred_country_select_widget


class DefaultRoleField(colander.SchemaNode):
    oid = "default_role"
    schema_type = colander.String
    widget = deform.widget.SelectWidget(values=default_role_options)
    default = "licenser"


# --- Schemas -----------------------------------------------------------------

class ProfileSchema(colander.Schema):
    firstname = FirstnameField(title=_("Firstname"))
    lastname = LastnameField(title=_("Lastname"))
    street = StreetField(title=_("Street"))
    postal_code = PostalCodeField(title=_("Postal Code"))
    city = CityField(title=_("City"))
    country = CountryField(title=_("Country"))
    email = EmailField(title=_("Email"))
    password = PasswordField(
        title=_("Password"),
        description=_("Leave password empty if you don't want to change it")
    )
    default_role = DefaultRoleField(title=_("Default Role"))


# --- Forms -------------------------------------------------------------------

def edit_profile_form(request):
    form = deform.Form(
        schema=ProfileSchema(
            validator=validate_unique_user_email).bind(request=request),
        buttons=[
            deform.Button('submit', _("Submit"))
        ]
    )
    return form
