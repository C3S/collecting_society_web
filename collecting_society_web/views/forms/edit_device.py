# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import deform

from portal_web.models import (
    Tdb
)
from .add_device import AddDeviceSchema
from portal_web.views.forms import FormController
from ...services import _
from ...models import Device


log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class EditDevice(FormController):
    """
    form controller for edit of devices
    """

    def controller(self):
        self.form = edit_device_form(self.request)
        if self.submitted():
            if self.validate():
                self.update_device()
        else:
            self.edit_device()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def edit_device(self):
        device = self.context.device

        # set appstruct
        self.appstruct = {
            'general': {
                'name': device.name,
                'uuid': device.uuid,
            },
            'os': {
                'os_name': device.os_name or '',
                'os_version': device.os_version or ''
            },
            'software': {
                'software_name': device.software_name or '',
                'software_version': device.software_version or '',
                'software_vendor': device.software_vendor or ''
            }
        }

        # render
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def update_device(self):
        web_user = self.request.web_user
        device = self.context.device

        # generate vlist
        _device = {
            'name': self.appstruct['general']['name'],
            'uuid': device.uuid,
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

        # update device and check webuser
        device_in_database = Device.search_by_uuid(
            self.appstruct['general']['uuid'])
        if (device_in_database and
                web_user == device_in_database.web_user):
            device.write([device], _device)
            
            # user feedback
            log.info("edit device successful for %s: %s" % (web_user, device))
            self.request.session.flash(
                _(u"Device edited:  ${name} (${uuid})",
                  mapping={'name': device.name,
                           'uuid': device.uuid}),
                'main-alert-success'
            )
        else:
            log.info("tried to edit device and write with wrong webuser %s: %s"
                     % (web_user, device))
            # user feedback
            log.info("edit device successful for %s: %s" % (web_user, device))
            self.request.session.flash(
                _(u"Device ${name} edited but device id ${uuid} hasn't changed",
                  mapping={'name': device.name,
                           'uuid': device.uuid}),
                'main-alert-warning'
            )                     
            
        # redirect
        self.redirect()


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Widgets -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

# --- Schemas -----------------------------------------------------------------

# --- Forms -------------------------------------------------------------------

def edit_device_form(request):
    return deform.Form(
        schema=AddDeviceSchema().bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )