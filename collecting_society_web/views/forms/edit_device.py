# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import deform

from portal_web.models import (
    Tdb,
    Party,
    WebUser
)
from portal_web.views.forms import FormController
from ...models import Device
# >>>>>>>>>>>>>>>> from .add_device import AddDeviceSchema

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class EditDevice(FormController):
    """
    form controller for edit of devices
    """

    def controller(self):
        # self.form = edit_device_form(self.request)
        # if self.submitted():
        #     if self.validate():
        #         self.update_device()
        # else:
        #     self.edit_device()
        # return self.response
        return {}
