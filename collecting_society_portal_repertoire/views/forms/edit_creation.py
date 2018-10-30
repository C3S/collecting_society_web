# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging
import deform

from collecting_society_portal.models import Tdb
from collecting_society_portal.views.forms import FormController

from ...services import _
from ...models import (
    Creation,
    Content
)
from .add_creation import (
    AddCreationSchema,
    validate_content
)

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class EditCreation(FormController):
    """
    form controller for edit creation
    """

    def controller(self):
        self.form = edit_creation_form(self.request)
        if self.submitted():
            if self.validate():
                self.update_creation()
        else:
            self.edit_creation()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def edit_creation(self):
        """
        initializes form with existing values of the Release entry
        """
        c = self.context.creation

        # set appstruct
        self.appstruct = {
            'metadata': {
                'title':
                    c.title or '',
                'artist':
                    c.artist.id,
                'releases':
                    [unicode(release.id) for release in c.releases]
            },
            # 'contributions': {
            #     'contributions':
            #         [
            #             {
            #                 'type': contribution.type,
            #                 'artist': contribution.artist
            #             }
            #             for contribution in c.contributions
            #         ]
            # },
            # 'relations': {
            # },
            # 'content': {
            # }
        }
        if c.contributions:
            _contributions = []
            for contribution in c.contributions:
                _contributions.append({
                    'type': contribution.type,
                    'artist': contribution.artist.id
                })
            self.appstruct['contributions'] = {
                'contributions': _contributions
            }

        # render form with init data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def update_creation(self):
        a = self.appstruct
        web_user = self.request.web_user
        creation = self.context.creation

        # generate vlist
        _creation = {
            'title': a['metadata']['title'],
            'artist': a['metadata']['artist'],
            'releases': a['metadata']['releases'],
        }

        # releases
        if a['metadata']['releases']:
            _creation['releases'] = []
            for release_id in a['metadata']['releases']:
                _creation['releases'].append(
                    (
                        'create',
                        [{
                            'release': release_id,
                            'title': a['metadata']['title'],
                            # TODO: manage different titles for releases
                            #       using a datatables control
                            # 'medium_number': TODO: medium_number
                            # 'track_number': TODO: track_number
                            # 'license ': TODO: license
                        }]
                    )
                )

        # contributions
        # if a['contributions']['contributions']:
        #     _creation['contributions'] = []
        #     for contribution in a[
        #             'contributions']['contributions']:
        #         _creation['contributions'].append(
        #             (
        #                 'create',
        #                 [{
        #                     'type': contribution['type'],
        #                     'artist': contribution['artist']
        #                 }]
        #             )
        #         )

        # derivation
        # if a['relations']['original_creations']:
        #     _creation['original_relations'] = []
        #     for original_creation in a[
        #             'relations']['original_creations']:
        #         _creation['original_relations'].append(
        #             (
        #                 'create',
        #                 [{
        #                     'original_creation': original_creation['creation'],
        #                     'allocation_type': original_creation['type']
        #                 }]
        #             )
        #         )

        # content
        if a['content']['content']:
            _creation['content'] = []
            for contentlistenty in a['content']['content']:
                content = Content.search_by_code(contentlistenty['code'])
                if content:
                    _creation['content'].append(
                        (
                            'add',
                            [content.id]
                        )
                    )

        # remove empty fields
        for index, value in _creation.items():
            if not value:
                del _creation[index]

        # update creation
        creation.write([creation], _creation)

        # user feedback
        log.info("creation edit successful for %s: %s" % (web_user, creation))
        self.request.session.flash(
            _(u"Creation edited: ") + creation.title
            + " ("+creation.code+")", 'main-alert-success'
        )

        # redirect
        self.redirect()


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Widgets -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

# --- Schemas -----------------------------------------------------------------

# --- Forms -------------------------------------------------------------------

def edit_creation_form(request):
    return deform.Form(
        schema=AddCreationSchema(
            title=_(u"Edit Release"),
            validator=validate_content).bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
