# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import colander
from pyramid.security import NO_PERMISSION_REQUIRED
from cornice import Service
from cornice.service import get_services
from cornice.validators import colander_body_validator
from cornice_swagger.swagger import CorniceSwagger

from ...services import _
from ...models import (
    CollectingSociety,
    TariffCategory,
    Artist,
    Creation,
    CreationContribution,
    CreationDerivative,
    CreationTariffCategory,
    CreationRole,
    Content
)

log = logging.getLogger(__name__)

_prefix = 'repertoire'


# --- schemas -----------------------------------------------------------------

# Create a body schema for our requests
class BodySchema(colander.MappingSchema):
    value = colander.SchemaNode(colander.String(),
                                description='My precious value')


# Create a response schema for our 200 responses
class OkResponseSchema(colander.MappingSchema):
    body = BodySchema()


# Aggregate the response schemas for get requests
response_schemas = {
    '200': OkResponseSchema(description='Return value')
}


_VALUES = {}


# --- resources ---------------------------------------------------------------

class UserResource(object):

    def __init__(self, request):
        self.request = request
        self.readonly = False


# --- service: licensing ------------------------------------------------------

licensing = Service(
    name='Creation',
    path='/repertoire/creations/{c3s_code}',
    description="provide licensing information about a creation",
    cors_enabled=True
)


# Create a service to serve our OpenAPI spec
swagger = Service(name='OpenAPI',
                  path='__api__',
                  description="OpenAPI documentation")


# --- API ---------------------------------------------------------------------


@licensing.get(permission=NO_PERMISSION_REQUIRED,
               tags=['creations'], response_schemas=response_schemas)
def get_value(request):
    """Returns the properties of a specific creation."""
    c3s_code = request.matchdict['c3s_code']
    # iswc = request.matchdict['iswc']
    # echoprint_fingerprint = request.matchdict['echoprint_fingerprint']
    # artist = request.matchdict['artist']
    # title = request.matchdict['title']

    creation = Creation.search_by_code(c3s_code)
    return {
            'artist': creation.artist.name,
            'title':  creation.title,
            'lyrics': creation.lyrics,
            'license': {
                'name':    creation.license.name,
                'code':    creation.license.code,
                'version': creation.license.version,
                'country': creation.license.country,
                'link':    creation.license.link
            },
            'derivatives': [d.code for d in creation.derivative_relations],
            'originals': [o.code for o in creation.original_relations],
            'releases': [r.release.title for r in creation.releases],
            'genres': [g.name for g in creation.genres],
            'styles': [s.name for s in creation.styles],
            'tariff_categories': [
                {
                    'name': t.name,
                    'code': t.code,
                    'description': t.description
                } for t in creation.tariff_categories]
           }


@licensing.put(permission=NO_PERMISSION_REQUIRED,
               tags=['creations'],
               validators=(colander_body_validator, ),
               schema=BodySchema(),
               response_schemas=response_schemas)
def set_value(request):
    """Sets the value and returns *True* or *False*."""

    key = request.matchdict['value']
    _VALUES[key] = request.json_body
    return _VALUES[key]


@swagger.get(permission=NO_PERMISSION_REQUIRED)
def openAPI_spec(request):
    my_generator = CorniceSwagger(get_services())
    my_spec = my_generator('Repertoire API', '0.1.0')
    return my_spec


# @licensing.get(
#     permission=NO_PERMISSION_REQUIRED,
#     validators=(colander_body_validator,),
#     factory=UserResource)
# def get_licensing(request):
#     data = request.validated
#
#     # response
#     return {
#         'data': data,
#     }
