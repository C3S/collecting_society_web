# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import operator
import logging
import colander

from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.httpexceptions import HTTPNotFound, HTTPConflict
from cornice import Service
from cornice.service import get_services
from cornice.validators import (
    colander_path_validator,
    colander_body_validator,
    colander_querystring_validator,
    colander_validator
)
from cornice_swagger.swagger import CorniceSwagger

from ...services import _
from ...models import (
    Creation,
    CreationIdentifier,
    CreationIdentifierSpace
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
    path=_prefix + '/info/creations/{native_id}',
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
                  description="OpenAPI documentation",
                  )


# --- API ---------------------------------------------------------------------

# ... Fields (Querystring Parameters) ...


class CodeField(colander.SchemaNode):
    oid = "native_id"
    name = "native_id"
    schema_type = colander.String
    validator = colander.Regex(r'^C\d{10}\Z')
    missing = ""


class ArtistField(colander.SchemaNode):
    oid = "artist"
    name = "artist"
    schema_type = colander.String
    validator = colander.Length(min=1)
    missing = ""


class TitleField(colander.SchemaNode):
    oid = "title"
    name = "title"
    schema_type = colander.String
    validator = colander.Length(min=1)
    missing = ""


def deferred_idspace_schemas_node(request):
    schema = colander.SchemaNode(
        colander.Mapping(),
        description=_(u"artist/title combinations, native code, or "
                      "foreign identifier spaces like isrc or iswc")
    )

    schema.add(CodeField(name='native_id', title=_("Native Code")))
    schema.add(ArtistField(name='artist', title=_("Artist")))
    schema.add(TitleField(name='title', title=_("Title")))

    for id_space in CreationIdentifierSpace.search_all():
        schema.add(
            colander.SchemaNode(
                colander.String(),
                oid=id_space.name,
                name=id_space.name,
                missing=""
                )
            )

    return schema


def deferred_querystring_validator(request, schema=None, deserializer=None,
                                   **kwargs):
    """
    Workaround to trick cornice into digesting a deferred schemas_node
    as root node.
    """
    if callable(schema):
        schema = schema(request)
    return colander_querystring_validator(request, schema, deserializer,
                                          **kwargs)


# ... parameter processing ...


@licensing_info.get(permission=NO_PERMISSION_REQUIRED,
                    tags=['creations'], response_schemas=response_schemas)
def get_licensing_info(request):
    """
    Returns the properties of a specific creation that
    is identified using the common REST scheme with
    the native code following the creation object.

    Example URL:
        http://api.collecting_society.test/licensing/info/creations/C0000012345

    """
    native_id = request.matchdict['native_id']
    return creation_data(native_id, 100)  # this is the code, 100% sure!


@licensing_info_multicode.get(permission=NO_PERMISSION_REQUIRED,
                              tags=['creations'],
                              schema=deferred_idspace_schemas_node,
                              validators=(deferred_querystring_validator,),
                              response_schemas=response_schemas)
def get_licensing_info_multicode(request):
    """
    Returns the properties of a specific creation
    that is identified using multiple identifiers,
    which are provided as querystring parameters.

    Example URL:
        http://api.collecting_society.test/licensing/info/creations?
        native_id=C0000000001&artist=Registered Name 001
        &title=Title of Song 001&ISRC=DES23445671&ISWC=DEX034567881
    """
    multicode = request.validated
    scores = {}  # count hits for creation codes identified by parameters
    number_of_identifiers_given = 0

    # 1st special case: artistname / tracktitle as composite identifier
    if ('artist' in multicode and 'title' in multicode and
            multicode['artist'] and multicode['title']):
        number_of_identifiers_given = number_of_identifiers_given + 1
        cs = Creation.search_by_artistname_and_title(multicode['artist'],
                                                     multicode['title'])
        if cs:
            c = cs[0]
            if c.code in scores:
                scores[c.code] = scores[c.code] + 1
            else:
                scores[c.code] = 1
    if 'artist' in multicode:
        del multicode['artist']
    if 'title' in multicode:
        del multicode['title']

    # 2nd special case: the native code of the creation:
    if 'native_id' in multicode and multicode['native_id']:
        number_of_identifiers_given = number_of_identifiers_given + 1
        c = Creation.search_by_code(multicode['native_id'])
        if c:
            if c.code in scores:
                scores[c.code] = scores[c.code] + 1
            else:
                scores[c.code] = 1
        del multicode['native_id']

    # TODO: 3rd special case: audio fingerprint
    # ...
    # ...

    # last (general) case: search in foreign id spaces defined in
    #                      CreationIdentifierSpace, e.g. isrc, iswc ...
    foreign_idspaces = [space.name for space in
                        CreationIdentifierSpace.search_all()]
    for queried_space_id in multicode:
        if (queried_space_id in foreign_idspaces and
                multicode[queried_space_id]):
            number_of_identifiers_given = number_of_identifiers_given + 1
            cid = CreationIdentifier.search_by_spacecode(queried_space_id,
                                                         multicode[
                                                             queried_space_id])
            if cid:  # found creation via foreign id?
                c = cid.creation
                if c.code in scores:
                    scores[c.code] = scores[c.code] + 1
                else:
                    scores[c.code] = 1

    # nothing found?
    number_of_hits = sum(count for count in scores.values())
    if number_of_hits == 0:
        raise HTTPNotFound

    sorted_scores = sorted(scores.items(), key=operator.itemgetter(1))
    best_matched_creation_code = sorted_scores[-1][0]
    best_matched_creation_score = sorted_scores[-1][1]
    final_score = int(100 * best_matched_creation_score
                      / number_of_identifiers_given)
    # TODO: raise HTTPConflict if result is ambigous e.g. if the
    #       codes with the highest scores > 1 hav equal scores.
    #       Alternatively have a priority which code to use in this case.

    return creation_data(best_matched_creation_code, final_score)


def creation_data(code, score):
    """
    Returns the properties of a specific creation, identified by the code.

    Args:
        creation code (String): native (C3S) code, i.e "C0000000123"
        score (Int): certainty in %, derived from the query parameter(s)
                     (to be returned in the result dict)

    Return:
        creation record (Dictionary) including the score

    Exceptions:
        HTTPNotFound, if creation can't be found from the code
    """
    # iswc = request.matchdict['iswc']
    # echoprint_fingerprint = request.matchdict['echoprint_fingerprint']
    # artist = request.matchdict['artist']
    # title = request.matchdict['title']

    creation = Creation.search_by_code(code)
    if not creation:
        raise HTTPNotFound

    # assemble creations foreign identifier list
    cfids = {}
    for cfid in creation.identifiers:
        cfids[cfid.id_space.name] = cfid.id_code

    # assemble rightsholders
    rightsholders = []
    for crh in creation.rightsholders:
        rightsholders.add({
            'rightsholder_subject': crh.rightsholder_subject.code,
            'rightsholder_object': crh.rightsholder_object.code,
            'contribution': crh.contribution,
            # 'successor': crh.successor,
            # 'instrument': ?
            'right': crh.right,
            'valid_from': crh.valid_from,
            'valid_to': crh.valid_to,
            'country': crh.country.name,
            'collecting_society': crh.collecting_society.name
        })

    return {
            'native_id': creation.code,
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
            'derivatives': [d.derivative_creation.code for d in
                            creation.derivative_relations],
            'originals': [o.original_creation.code for o in
                          creation.original_relations],
            'releases': [r.release.title for r in creation.releases],
            'genres': [g.name for g in creation.genres],
            'styles': [s.name for s in creation.styles],
            'tariff_categories': [
                {
                    'name': t.category.name,
                    'code': t.category.code,
                    'description': t.category.description
                } for t in creation.tariff_categories],
            'foreign_ids': cfids,
            'rightsholders': rightsholders,
            'score': score
           }


# ... swagger/openAPI stuff ...


@swagger.get(permission=NO_PERMISSION_REQUIRED)
def openAPI_spec(request):
    my_generator = CorniceSwagger(get_services())
    my_generator.summary_docstrings = True
    my_spec = my_generator('Repertoire API', '0.1.0')
    return my_spec


# ... some test code TODO: delete ...

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
#
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
