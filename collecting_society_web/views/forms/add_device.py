# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import colander
import deform

from portal_web.models import (
    Tdb,
    Party,
    WebUser
)
from portal_web.views.forms import (
    FormController
)

from ...models import Device

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class AddDevice(FormController):
    """
    form controller for creation of devices
    """

    def controller(self):
        return {}
