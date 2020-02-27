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
    Release as ReleaseModel,
    ReleaseIdentifier,
    ReleaseIdentifierSpace
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
        "code because release was found"
    ),
    '404': ResponseSchema(
        description="Return 'http not found' response code a release with "
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
    validator = colander.Regex(r'^R\d{10}\Z')


class ReleaseField(colander.SchemaNode):
    oid = "release"
    name = "release"
    schema_type = colander.String
    validator = colander.Length(min=1)
    missing = ""


class ReleaseGetSchema(colander.Schema):
    code = CodeField(title=_(u"Native Code"))


def deferred_idspace_schemas_node(request):
    schema = colander.SchemaNode(
        colander.Mapping(),
        description=_(u"release name, native code, or "
                      "foreign identifier spaces like isrc")
    )

    schema.add(CodeField(name='native_id', title=_("Native Code"),
                         missing=""))
    schema.add(ReleaseField(name='release', title=_("Release")))

    for id_space in ReleaseIdentifierSpace.search_all():
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


@resource(collection_path=apiversion + '/releases',
          path=apiversion + '/releases/{native_id}',
          permission=NO_PERMISSION_REQUIRED)
class Release(ResourceBase):

    def __acl__(self):
        return [(Allow, Everyone, 'view')]

    @view(tags=['releases'],
          schema=deferred_idspace_schemas_node,
          validators=(deferred_querystring_validator,),
          response_schemas=response_schemas)
    def collection_get(self, permission='view'):
        """
        Returns the properties of a specific release
        that is identified using multiple identifiers,
        which are provided as querystring parameters.

        Example URL:
            http://api.collecting_society.test/v1/releases?
            native_id=R0000000001&release=Release 001
            &GRid=A1-ABCDE-0000000001-M&EAN/UPC=0000000000001
        """
        multicode = self.request.validated
        scores = {}  # count hits for release codes identified by parameters
        number_of_identifiers_given = 0

        # 1st special case: release name  identifier
        if 'release' in multicode and multicode['release']:
            releases = ReleaseModel.search_by_name(multicode['release'])
            if not releases:
                number_of_identifiers_given += 1
            else:
                for release in releases:
                    number_of_identifiers_given += 1
                    if release.code in scores:
                        scores[release.code] += 1
                    else:
                        scores[release.code] = 1
        if 'release' in multicode:
            del multicode['release']

        # 2nd special case: the native code of the release:
        if 'native_id' in multicode and multicode['native_id']:
            number_of_identifiers_given += 1
            c = ReleaseModel.search_by_code(multicode['native_id'])
            if c:
                if c.code in scores:
                    scores[c.code] = scores[c.code] + 1
                else:
                    scores[c.code] = 1
            del multicode['native_id']

        # last (general) case: search in foreign id spaces defined in
        #                      ReleaseIdentifierSpace, e.g. isrc, iswc ...
        foreign_idspaces = [space.name for space in
                            ReleaseIdentifierSpace.search_all()]
        for queried_space_id in multicode:
            if (queried_space_id in foreign_idspaces and
                    multicode[queried_space_id]):
                number_of_identifiers_given += 1
                aid = ReleaseIdentifier.search_by_spacecode(
                    queried_space_id, multicode[queried_space_id])
                if aid:  # found release via foreign id?
                    c = aid.release
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

        return self.release_data(sorted_scores)

    @view(tags=['releases'],
          schema=ReleaseGetSchema,
          validators=(colander_path_validator,),
          response_schemas=response_schemas)
    def get(self, permission='view'):
        """
        Returns the properties of a specific release that
        is identified using the common REST scheme with
        the native code following the release object.

        Example URL:
            http://api.collecting_society.test/v1/releases/R0000012345

        """
        return self.release_data([(self.request.matchdict['native_id'], 100)])

    def release_data(self, sorted_scores):
        """
        Returns the properties of the found releases.

        Args:
            sorted_scores [(String, Int)]: native (C3S) code, i.e "R0000000123"
                together with a score certainty in %, derived from the query
                parameter(s) (to be returned in the result dict)

        Return:
            release record (Dictionary) including the score

        Exceptions:
            HTTPNotFound, if release can't be found from the code
        """

        releases = []
        for code, score in sorted_scores:
            release = ReleaseModel.search_by_code(code)
            if not release:
                raise HTTPNotFound

            # assemble releases foreign identifier list
            rfids = {}
            for rfid in release.identifiers:
                rfids[rfid.space.name] = rfid.id_code

            # assemble rightsholders
            rightsholders = []
            for rrh in release.rightsholders:
                rightsholders.append({
                    'rightsholder_subject': rrh.rightsholder_subject.code,
                    'rightsholder_object': rrh.rightsholder_object.code,
                    'contribution': rrh.contribution,
                    # 'successor': rrh.successor,
                    # 'instrument': ?
                    'right': rrh.right,
                    'valid_from': str(rrh.valid_from),
                    'valid_to': str(rrh.valid_to),
                    'country': rrh.country.name,
                    'collecting_society': rrh.collecting_society.name
                })

            releases.append({
                'native_id': release.code,
                'title': release.title,
                'foreign_ids': rfids,
                # 'picture_data': release.picture_data,
                # 'picture_data_md5': release.picture_data_md5,
                # 'picture_thumbnail_data': release.picture_thumbnail_data,
                # 'picture_data_mime_type': release.picture_data_mime_type,
                'genres': [rg.name for rg in release.genres],
                'styles': [rs.name for rs in release.styles],
                'warning': release.warning,
                'copyright_date': str(release.copyright_date),
                'production_date': str(release.production_date),
                'producers': [pd.code for pd in release.producers],
                'release_date': str(release.release_date),
                'release_cancellation_date': str(
                    release.release_cancellation_date),
                'online_release_date': str(release.online_release_date),
                'online_cancellation_date': str(
                    release.online_cancellation_date),
                'distribution_territory': release.distribution_territory,
                'label': release.label.name,
                'label_catalog_number': release.label_catalog_number,
                'publisher': release.publisher.name,
                'neighbouring_rights_societies': [
                    nrs.name for nrs in release.neighbouring_rights_societies],
                'published': release.published,

                'rightsholders': rightsholders,
                'score': str(score)
            })

        return releases
