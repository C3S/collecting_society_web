# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import operator
import logging
import colander

from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.authorization import (
    Allow,
    Everyone
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
    Artist as ArtistModel,
    ArtistIdentifier,
    ArtistIdentifierSpace
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
        "code because artist was found"
    ),
    '404': ResponseSchema(
        description="Return 'http not found' response code a artist with "
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
    validator = colander.Regex(r'^A\d{10}\Z')


class ArtistField(colander.SchemaNode):
    oid = "artist"
    name = "artist"
    schema_type = colander.String
    validator = colander.Length(min=1)
    missing = ""


class ArtistGetSchema(colander.Schema):
    code = CodeField(title=_(u"Native Code"))


def deferred_idspace_schemas_node(request):
    schema = colander.SchemaNode(
        colander.Mapping(),
        description=_(u"artist name, native code, or "
                      "foreign identifier spaces like ipn")
    )

    schema.add(CodeField(name='native_id', title=_("Native Code"),
                         missing=""))
    schema.add(ArtistField(name='artist', title=_("Artist")))

    for id_space in ArtistIdentifierSpace.search_all():
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


# --- service for artits api --------------------------------------------------


@resource(collection_path=apiversion + '/artists',
          path=apiversion + '/artists/{native_id}',
          permission=NO_PERMISSION_REQUIRED)
class Artist(ResourceBase):

    def __acl__(self):
        return [(Allow, Everyone, 'view')]

    @view(tags=['artists'],
          schema=deferred_idspace_schemas_node,
          validators=(deferred_querystring_validator,),
          response_schemas=response_schemas)
    def collection_get(self, permission='view'):
        """
        Returns the properties of a specific artist
        that is identified using multiple identifiers,
        which are provided as querystring parameters.

        Example URL:
            http://api.collecting_society.test/v1/artists?
            native_id=C0000000001&artist=Registered Name 001
            &title=Title of Song 001&ISRC=DE-A00-20-00001&ISWC=T-000.000.001-C
        """
        multicode = self.request.validated
        scores = {}  # count hits for artist codes identified by parameters
        number_of_identifiers_given = 0

        # 1st special case: artist name  identifier
        if 'artist' in multicode and multicode['artist']:
            artists = ArtistModel.search_by_name(multicode['artist'])
            if not artists:
                number_of_identifiers_given += 1
            else:
                for artist in artists:
                    number_of_identifiers_given += 1
                    if artist.code in scores:
                        scores[artist.code] += 1
                    else:
                        scores[artist.code] = 1
        if 'artist' in multicode:
            del multicode['artist']

        # 2nd special case: the native code of the artist:
        if 'native_id' in multicode and multicode['native_id']:
            number_of_identifiers_given += 1
            c = ArtistModel.search_by_code(multicode['native_id'])
            if c:
                if c.code in scores:
                    scores[c.code] = scores[c.code] + 1
                else:
                    scores[c.code] = 1
            del multicode['native_id']

        # last (general) case: search in foreign id spaces defined in
        #                      ArtistIdentifierSpace, e.g. isrc, iswc ...
        foreign_idspaces = [space.name for space in
                            ArtistIdentifierSpace.search_all()]
        for queried_space_id in multicode:
            if (queried_space_id in foreign_idspaces and
                    multicode[queried_space_id]):
                number_of_identifiers_given += 1
                aid = ArtistIdentifier.search_by_spacecode(
                    queried_space_id, multicode[queried_space_id])
                if aid:  # found artist via foreign id?
                    c = aid.artist
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

        return self.artist_data(sorted_scores)

    @view(tags=['artists'],
          schema=ArtistGetSchema,
          validators=(colander_path_validator,),
          response_schemas=response_schemas)
    def get(self, permission='view'):
        """
        Returns the properties of a specific artist that
        is identified using the common REST scheme with
        the native code following the artist object.

        Example URL:
            http://api.collecting_society.test/v1/artists/C0000012345

        """
        return self.artist_data([(self.request.matchdict['native_id'], 100)])

    def artist_data(self, sorted_scores):
        """
        Returns the properties of the found artists.

        Args:
            sorted_scores [(String, Int)]: native (C3S) code, i.e "C0000000123"
                together with a score certainty in %, derived from the query
                parameter(s) (to be returned in the result dict)

        Return:
            artist record (Dictionary) including the score

        Exceptions:
            HTTPNotFound, if artist can't be found from the code
        """

        artists = []
        for code, score in sorted_scores:
            artist = ArtistModel.search_by_code(code)
            if not artist:
                raise HTTPNotFound

            # assemble artists foreign identifier list
            afids = {}
            for afid in artist.identifiers:
                afids[afid.space.name] = afid.id_code

            artists.append({
                'native_id': artist.code,
                'name': artist.name,
                'foreign_ids': afids,
                # 'party': artist.party,
                'group': artist.group,
                'solo_artists': [sa.code for sa in artist.solo_artists],
                'group_artists': [ga.code for ga in artist.group_artists],
                'releases': [rl.code for rl in artist.releases],
                'creations': [cr.code for cr in artist.creations],
                # 'access_parties': artist.access_parties,
                # 'invitation_token': artist.invitation_token,
                'description': artist.description,
                # 'picture_data': artist.picture_data,
                # 'picture_data_md5': artist.picture_data_md5,
                # 'picture_thumbnail_data': artist.picture_thumbnail_data,
                # 'picture_data_mime_type': artist.picture_data_mime_type,
                # 'payee': artist.payee,
                # 'payee_proposal': artist.payee_proposal,
                # 'payee_acceptances': artist.payee_acceptances,
                # 'valid_payee': artist.valid_payee,
                # 'bank_account_number': artist.bank_account_number,
                # 'bank_account_numbers': artist.bank_account_numbers,
                # 'bank_account_owner': artist.bank_account_owner
                'score': str(score)
            })

        return artists
