# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web
# flake8: noqa

# portal
from .register_webuser import RegisterWebuser
from .edit_profile import EditProfile

# licenser
from .add_artist import AddArtist
from .edit_artist import EditArtist
from .add_release import AddRelease
from .edit_release import EditRelease
from .add_creation import AddCreation
from .edit_creation import EditCreation

# licensee
from .add_device import AddDevice
from .edit_device import EditDevice
from .add_declaration_live import AddDeclarationLive
from .confirm_declaration_live import ConfirmDeclarationLive
from .add_location import AddLocation
from .edit_location import EditLocation
from .finalize_declaration_live import FinalizeDeclarationLive
