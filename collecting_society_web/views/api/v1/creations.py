# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import operator
import logging
import colander

from pyramid.security import (
    Allow,
    Everyone,
    NO_PERMISSION_REQUIRED,
)
from pyramid.httpexceptions import HTTPNotFound
from cornice.resource import resource, view
from cornice.validators import (
    colander_path_validator,
    colander_querystring_validator
)

from portal_web.resources import ResourceBase
from ....services import _
from ....models import (
    Creation as CreationModel,
    CreationIdentifier,
    CreationIdentifierSpace
)
from . import apiversion

log = logging.getLogger(__name__)


# --- schemas -----------------------------------------------------------------

class BodySchema(colander.MappingSchema):
    """Create a body schema for our requests"""
    value = colander.SchemaNode(colander.String(),
                                description='Some JSON returned')


class ResponseSchema(colander.MappingSchema):
    """Create a response schema for our 200 responses"""
    body = BodySchema()


# Aggregate the response schemas for get requests
response_schemas = {
    '200': ResponseSchema(
        description="Return 'http ok' response "
        "code because creation was found"
    ),
    '404': ResponseSchema(
        description="Return 'http not found' response code a creation with "
        "matching id couldn't be found in the database"
    )
}


_VALUES = {}


# --- resources ---------------------------------------------------------------

class UserResource(object):

    def __init__(self, request):
        self.request = request
        self.readonly = False


# --- API ---------------------------------------------------------------------

# ... Fields (Querystring Parameters) ...


class CodeField(colander.SchemaNode):
    oid = "native_id"
    name = "native_id"
    schema_type = colander.String
    validator = colander.Regex(r'^C\d{10}\Z')


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


class CreationGetSchema(colander.Schema):
    code = CodeField(title=_(u"Native Code"))


def deferred_idspace_schemas_node(request):
    schema = colander.SchemaNode(
        colander.Mapping(),
        description=_(u"artist/title combinations, native code, or "
                      "foreign identifier spaces like isrc or iswc")
    )

    schema.add(CodeField(name='native_id', title=_("Native Code"),
                         missing=""))
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


# --- service for creation api ------------------------------------------------


@resource(collection_path=apiversion + '/creations',
          path=apiversion + '/creations/{native_id}',
          permission=NO_PERMISSION_REQUIRED)
class Creation(ResourceBase):

    def __acl__(self):
        return [(Allow, Everyone, 'view')]

    @view(tags=['creations'],
          schema=deferred_idspace_schemas_node,
          validators=(deferred_querystring_validator,),
          response_schemas=response_schemas)
    def collection_get(self, permission='view'):        
        """
        Returns the properties of a specific creation
        that is identified using multiple identifiers,
        which are provided as querystring parameters.

        Example URL:
            http://api.collecting_society.test/v1/creations?
            native_id=C0000000001&artist=Registered Name 001
            &title=Title of Song 001&ISRC=DE-A00-20-00001&ISWC=T-000.000.001-C
        """
        multicode = self.request.validated
        scores = {}  # count hits for creation codes identified by parameters
        number_of_identifiers_given = 0

        # 1st special case: artistname / tracktitle as composite identifier
        if ('artist' in multicode and 'title' in multicode and
                multicode['artist'] and multicode['title']):
            number_of_identifiers_given += 1
            cs = CreationModel.search_by_artistname_and_title(
                multicode['artist'], multicode['title'])
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
            number_of_identifiers_given += 1
            c = CreationModel.search_by_code(multicode['native_id'])
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
                number_of_identifiers_given += 1
                cid = CreationIdentifier.search_by_spacecode(
                    queried_space_id, multicode[queried_space_id])
                if cid:  # found creation via foreign id?
                    c = cid.creation
                    if c.code in scores:
                        scores[c.code] += 1
                    else:
                        scores[c.code] = 1

        # nothing found?
        number_of_hits = sum(count for count in scores.values())
        if number_of_hits == 0:
            raise HTTPNotFound

        # sort: highest score first
        for code in scores.keys():
            scores[code] = int(100 * scores[code] 
                               / number_of_identifiers_given)
        sorted_scores = sorted(scores.items(), key=operator.itemgetter(1),
                               reverse=True)

        return self.creation_data(sorted_scores)

    @view(tags=['creations'],
          schema=CreationGetSchema,
          validators=(colander_path_validator,),
          response_schemas=response_schemas)
    def get(self, permission='view'):
        """
        Returns the properties of a specific creation that
        is identified using the common REST scheme with
        the native code following the creation object.

        Example URL:
            http://api.collecting_society.test/v1/creations/C0000012345

        """
        return self.creation_data([(self.request.matchdict['native_id'], 100)])

    def creation_data(self, sorted_scores):
        """
        Returns the properties of the found creations.

        Args:
            sorted_scores [(String, Int)]: native (C3S) code, i.e "C0000000123"
                together with a score certainty in %, derived from the query
                parameter(s) (to be returned in the result dict)

        Return:
            creation record (Dictionary) including the score

        Exceptions:
            HTTPNotFound, if creation can't be found from the code
        """

        creations = []
        for code, score in sorted_scores:
            creation = CreationModel.search_by_code(code)
            if not creation:
                raise HTTPNotFound

            # assemble creations foreign identifier list
            cfids = {}
            for cfid in creation.identifiers:
                cfids[cfid.space.name] = cfid.id_code

            # assemble rightsholders
            rights = []
            for crh in creation.rightsholders:
                rights.append({
                    'rightsholder': crh.rightsholder.code,
                    'rightsobject': crh.rightsobject.code,
                    'contribution': crh.contribution,
                    # 'successor': crh.successor,
                    # 'instrument': ?
                    'type_of_right': crh.type_of_right,
                    'valid_from': str(crh.valid_from),
                    'valid_to': str(crh.valid_to),
                    'country': crh.country.name,
                    'collecting_society': crh.collecting_society.name or None
                })

            creations.append({
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
                'originals':   [o.original_creation.code for o in
                                creation.original_relations],
                'releases':    [r.release.code for r in creation.releases],
                'genres':      [g.name for g in creation.genres],
                'styles':      [s.name for s in creation.styles],
                'tariff_categories': [
                    {
                        'name': t.category.name,
                        'code': t.category.code,
                        'description': t.category.description
                    } for t in creation.tariff_categories],
                'foreign_ids': cfids,
                'rights': rights,
                'score': str(score)
            })

        return creations
