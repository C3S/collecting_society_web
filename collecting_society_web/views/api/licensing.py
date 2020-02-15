# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import logging
import colander
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.httpexceptions import HTTPNotFound, HTTPConflict
from cornice import Service
from cornice.service import get_services
from cornice.validators import colander_path_validator, colander_body_validator, colander_querystring_validator, colander_validator
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

_prefix = 'licensing'


# --- schemas -----------------------------------------------------------------

class BodySchema(colander.MappingSchema):
    """Create a body schema for our requests"""
    value = colander.SchemaNode(colander.String(),
                                description='My precious value')

class ResponseSchema(colander.MappingSchema):
    """Create a response schema for our 200 responses"""
    body = BodySchema()


# Aggregate the response schemas for get requests
response_schemas = {
    '200': ResponseSchema(
        description="Return 'http ok' response " +
        "code because creation was found"
    ),
    '404': ResponseSchema(
        description="Return 'http not found' response code a creation with "
        "matching id couldn't be found in the database"
    ),
    '409': ResponseSchema(
        description="Return 'http conflict' response code because creation "
        "couldn't be identified because the ids refer to different creations"
    )
}


_VALUES = {}


# --- resources ---------------------------------------------------------------

class UserResource(object):

    def __init__(self, request):
        self.request = request
        self.readonly = False


# --- service: licensing_info -----------------------------------------------

licensing_info = Service(
    name=_prefix + 'info',
    path=_prefix + '/info/creations/{code}',
    description="provide licensing information about a creation",
    cors_enabled=True
)


licensing_info_multicode = Service(
    name=_prefix + 'infomulticode',
    path=_prefix + '/info/creations',
    description="provide licensing information about a creation",
    cors_enabled=True
)


# Create a service to serve our OpenAPI spec
swagger = Service(name='OpenAPI',
                  path='__api__',
                  description="OpenAPI documentation")


# --- API ---------------------------------------------------------------------


@licensing_info.get(permission=NO_PERMISSION_REQUIRED,
                    tags=['creations'], response_schemas=response_schemas)
def get_licensing_info(request):
    """Returns the properties of a specific creation"""
    code = request.matchdict['code']
    # iswc = request.matchdict['iswc']
    # echoprint_fingerprint = request.matchdict['echoprint_fingerprint']
    # artist = request.matchdict['artist']
    # title = request.matchdict['title']
    # TODO: raise HTTPConflict when multiple ids lead to different creations

    creation = Creation.search_by_code(code)
    if not creation:
        raise HTTPNotFound
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


class CodeField(colander.SchemaNode):
    oid = "code"
    schema_type = colander.String
    validator = colander.Regex(r'^C\d{10}\Z')
    missing = ""


class ArtistField(colander.SchemaNode):
    oid = "artist"
    schema_type = colander.String
    validator = colander.Length(min=1)
    missing = ""


class TitleField(colander.SchemaNode):
    oid = "title"
    schema_type = colander.String
    validator = colander.Length(min=1)
    missing = ""


class IdSchema(colander.MappingSchema):
    code = CodeField(title=_("Code"))
    artist = ArtistField(title=_("Artist"))
    title = TitleField(title=_("Title"))


@licensing_info_multicode.get(permission=NO_PERMISSION_REQUIRED,
                              tags=['creations'],
                              schema=IdSchema,
                              validators=(colander_querystring_validator,),
                              response_schemas=response_schemas)
def get_licensing_info_multicode(request):
    """Returns the properties of a specific creation"""
    data = request.validated
    return data
    # iswc = request.matchdict['iswc']
    # echoprint_fingerprint = request.matchdict['echoprint_fingerprint']
    # artist = request.matchdict['artist']
    # title = request.matchdict['title']
    # TODO: raise HTTPConflict when multiple ids lead to different creations?


# @licensing.put(permission=NO_PERMISSION_REQUIRED,
#                tags=['creations'],
#                validators=(colander_body_validator, ),
#                schema=BodySchema(),
#                response_schemas=response_schemas)
# def set_value(request):
#     """Sets the value and returns *True* or *False*."""
# 
#     key = request.matchdict['value']
#     _VALUES[key] = request.json_body
#     return _VALUES[key]


@swagger.get(permission=NO_PERMISSION_REQUIRED)
def openAPI_spec(request):
    my_generator = CorniceSwagger(get_services())
    my_generator.summary_docstrings = True
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
