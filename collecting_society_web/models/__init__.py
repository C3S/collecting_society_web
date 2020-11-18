# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web
# flake8: noqa

from .collecting_society import CollectingSociety
from .tariff_category import TariffCategory

from .artist import Artist
from .artist_identifier import ArtistIdentifier
from .artist_identifier_space import ArtistIdentifierSpace
from .release import Release
from .release_identifier import ReleaseIdentifier
from .release_identifier_space import ReleaseIdentifierSpace
from .creation import Creation
from .creation_contribution import CreationContribution
from .creation_derivative import CreationDerivative
from .creation_role import CreationRole
from .creation_tariff_category import CreationTariffCategory
from .creation_identifier import CreationIdentifier
from .creation_identifier_space import CreationIdentifierSpace
from .creation_rightsholder import CreationRightsholder
from .creation_rightsholder_instrument import CreationRightsholderInstrument
from .content import Content
from .genre import Genre
from .instrument import Instrument
from .style import Style
from .label import Label
from .publisher import Publisher
from .license import License
from .track import Track
from .device import Device
from .event import Event
from .location import Location
from .location_category import LocationCategory
from .location_space import LocationSpace
from .location_space_category import LocationSpaceCategory
from .declaration import Declaration
from .utilisation import Utilisation
from .website import Website