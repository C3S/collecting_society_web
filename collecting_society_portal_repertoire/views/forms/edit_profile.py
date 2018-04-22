# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import colander
import deform
from pkg_resources import resource_filename
import logging
import re

from pyramid.threadlocal import get_current_request
from pyramid.i18n import get_localizer

from collecting_society_portal.models import (
    Tdb,
    WebUser
)
from collecting_society_portal.views.forms import (
    FormController,
    deferred_file_upload_widget
)
from collecting_society_portal.services import send_mail
from ...services import _
#from ...models import Artist
from ...resources import ProfileResource

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class EditProfile(FormController):
    """
    form controller for editing the user profile
    """

    def controller(self):
        
        self.form = edit_profile_form(self.request)
        if not (self.submitted() and self.validate()):
            # initialize form
            #import rpdb2; rpdb2.start_embedded_debugger("supersecret", fAllowRemote = True)
            web_user = WebUser.current_web_user(self.request)
            self.appstruct = {
                'name': web_user.party.name or "",
                'firstname': web_user.party.firstname or "",
                'lastname': web_user.party.lastname or "",
                'email': web_user['email'] or ""
            }
            self.render(self.appstruct)
            pass
        else:  
            # submit validated data from form            
            self.change_profile()

        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=False)
    def change_profile(self):
        web_user = WebUser.current_web_user(self.request)
        web_user.party.firstname = self.appstruct['firstname'] #save separately
        web_user.party.lastname =  self.appstruct['lastname']  #for clarity
        web_user.party.name = (web_user.party.firstname + ' ' 
            + web_user.party.lastname)
            #self.appstruct['name'] TODO: generate name using a tryton trigger
        if self.appstruct['email'] != web_user.email:
            web_user.new_email = self.appstruct['email'] # needs email verification
            web_user.save()
            template_variables = {
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
        web_user.party.save()

        if self.appstruct['email'] == web_user.email:
            log.info("edit profile add successful for %s" % (web_user.party.name))
            self.request.session.flash(
                _(u"Profile changed for: ") + web_user.party.name,
                'main-alert-success'
            )
        else:
            log.info("edit profile add successful for %s, activation email sent."
                % (web_user.party.name))
            self.request.session.flash(
                _(u"Profile changed for: ") + web_user.party.name +
                _(u" -- activation email for new email address sent.") +
                _(u" Please check your (new) email inbox."),
                'main-alert-success'
            )

        self.redirect(ProfileResource, 'show')



# --- Validators --------------------------------------------------------------


def not_empty(value):
    """Ensure field has at least two characters in it."""
    if not value or len(value) < 2:
        return _(u"Please enter your name.")
    return True

def validate_unique_user_email(node, values, **kwargs): # multi-field validator
    """Check for valid email and prevent duplicate usernames."""

    request = node.bindings["request"]
    email_value = values["email"]
    current_web_user = WebUser.current_web_user(request)
    if email_value != current_web_user.email:
        # email has been changed: check if it conflicts with other webuser
        found_conflicting_web_user = WebUser.search_by_email(email_value)
        if found_conflicting_web_user:
            raise colander.Invalid(node, "Email address already taken")

    # finally, check email format
    if len(email_value) > 7:
        if re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email_value) != None:
            return
    raise colander.Invalid(node, "Invalid email address")

# --- Options -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------


#class NameField(colander.SchemaNode):
#    oid = "name"
#    schema_type = colander.String
#    validator = colander.Function(not_empty)


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
    #validator = colander.Function(validate_unique_user_email)


class PasswordField(colander.MappingSchema):
    oid = "password"
    schema_type = colander.String
    validator = colander.Length(min=8)
    widget = deform.widget.CheckedPasswordWidget()
    missing = ''


# --- Schemas -----------------------------------------------------------------

class ProfileSchema(colander.Schema):

    #name = NameField(
    #    title=_(u"Name")
    #)
    firstname = FirstnameField(
        title=_(u"Firstname")
    )
    lastname = LastnameField(
        title=_(u"Lastname")
    )
    email = EmailField(
        title=_(u"Email")
    )
    password = PasswordField(
        title=_(u"Password (leave empty if you don't want to change it)")
    )


# --- Forms -------------------------------------------------------------------

# custom template
def translator(term):
    return get_localizer(get_current_request()).translate(term)


def edit_profile_form(request):

    form = deform.Form(
        schema=ProfileSchema(
            validator=validate_unique_user_email).bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )

    return form