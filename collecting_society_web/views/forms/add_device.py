# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import colander
import deform
import uuid

from portal_web.models import (
    Tdb,
    Party,
    WebUser
)
from portal_web.views.forms import FormController
from ...services import _
from ...models import Device

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class AddDevice(FormController):
    """
    form controller for creation of devices
    """

    def controller(self):
        self.form = add_device_form(self.request)
        self.render()
        if self.submitted():
            if self.validate():
                self.create_device()
        else:
            self.init_device()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def init_device(self):
        """
        initializes form with arguments passed via url from Content/Uploads
        """

        if not self.appstruct:
            self.appstruct = {
                'general': {
                    'name': '',
                    'uuid': '',
                },
                'os': {
                    'os_name': '',
                    'os_version': ''
                },
                'software': {
                    'software_name': '',
                    'software_version': '',
                    'software_vendor': ''
                }
            }

        # add metadata from device uuid, name, etc. provided by client device as url params
        device_id = getattr(self.context, 'device_id', False)
        if device_id:
            self.appstruct['general']['uuid'] = device_id
        else:
            if not self.appstruct['general']['uuid']:
                self.appstruct['general']['uuid'] = str(uuid.uuid4())
        if not self.appstruct['general']['name']:
            self.appstruct['general']['name'] = getattr(
                self.context, 'device_name', False)
        if not self.appstruct['general']['name']:
            self.appstruct['general']['name'] = _("My Device")
        if not self.appstruct['os']['os_name']:
            self.appstruct['os']['os_name'] = getattr(
                self.context, 'os_name', False) or ''
        if not self.appstruct['os']['os_version']:
            self.appstruct['os']['os_version'] = getattr(
                self.context, 'os_version', False) or ''
        if not self.appstruct['software']['software_name']:
            self.appstruct['software']['software_name'] = getattr(
                self.context, 'software_name', False) or ''
        if not self.appstruct['software']['software_version']:
            self.appstruct['software']['software_version'] = getattr(
                self.context, 'software_version', False) or ''
        if not self.appstruct['software']['software_vendor']:
            self.appstruct['software']['software_vendor'] = getattr(
                self.context, 'software_vendor', False) or ''

        # render form with init data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def create_device(self):
        web_user = self.request.web_user

        # generate vlist
        _device = {
            'name': self.appstruct['general']['name'],
            'uuid': self.appstruct['general']['uuid'],
            'web_user': web_user,
            'os_name': self.appstruct['os']['os_name'],
            'os_version': self.appstruct['os']['os_version'],
            'software_name': self.appstruct['software']['software_name'],
            'software_version': self.appstruct['software']['software_version'],
            'software_vendor': self.appstruct['software']['software_vendor']
        }

        # remove empty fields
        for index, value in _device.items():
            if not value:
                del _device[index]

        # create device
        device = Device.create([_device])

        # user feedback
        if not device:
            log.info("device add failed for %s: %s" % (web_user, _device))
            self.request.session.flash(
                _(u"Device could not be added: ${reti}",
                  mapping={'reti': _device['title']}),
                'main-alert-danger'
            )
            self.redirect()
            return
        device = device[0]
        log.info("device add successful for %s: %s" % (web_user, device))
        self.request.session.flash(
            _(u"Device '${reti}' added to your account. Your device token is ${reco}.",
              mapping={'reti': device.name,
                       'reco': device.uuid}),
            'main-alert-success'
        )

        # redirect
        self.redirect()


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Widgets -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------


# -- General tab --

class NameField(colander.SchemaNode):
    oid = "name"
    schema_type = colander.String
    validator = colander.Length(min=1, min_err=_(
        "You need to provide a device name"))


class UuidField(colander.SchemaNode):
    oid = "uuid"
    schema_type = colander.String
    validator = colander.uuid


# -- OS tab --

class OSNameField(colander.SchemaNode):
    oid = "os_name"
    schema_type = colander.String
    missing = ""


class OSVersionField(colander.SchemaNode):
    oid = "os_version"
    schema_type = colander.String
    missing = ""


# -- Software tab --

class SoftwareNameField(colander.SchemaNode):
    oid = "software_name"
    schema_type = colander.String
    missing = ""


class SoftwareVersionField(colander.SchemaNode):
    oid = "software_version"
    schema_type = colander.String
    missing = ""


class SoftwareVendorField(colander.SchemaNode):
    oid = "software_vendor"
    schema_type = colander.String
    missing = ""


# --- Schemas -----------------------------------------------------------------

class GeneralSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    name = NameField(title=_(u"Name"))
    uuid = UuidField(title=_(u"Device ID"))


class OSSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    os_name = OSNameField(title=_(u"Name"))
    os_version = OSVersionField(title=_(u"Version"))


class SoftwareSchema(colander.Schema):
    widget = deform.widget.MappingWidget(template='navs/mapping')
    software_name = SoftwareNameField(title=_(u"Name"))
    software_version = SoftwareVersionField(title=_(u"Version"))
    software_vendor = SoftwareVendorField(title=_(u"Vendor"))


class AddDeviceSchema(colander.Schema):
    widget = deform.widget.FormWidget(template='navs/form', navstyle='tabs')
    general = GeneralSchema(title=_(u"General"))
    os = OSSchema(title=_(u"Operating System"))
    software = SoftwareSchema(title=_(u"Software"))


# --- Forms -------------------------------------------------------------------

def add_device_form(request):
    return deform.Form(
        schema=AddDeviceSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
