# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging
import deform

from collecting_society_portal.models import Tdb
from collecting_society_portal.views.forms import FormController

from ...services import _
from ...models import (
    Creation,
    Content,
    CreationDerivative
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
        c = self.context.creation

        # set appstruct
        self.appstruct = {
            'metadata': {
                'title':
                    c.title or '',
                'artist':
                    c.artist.id,
                #'releases':   -> relation maintained in Release form only
                #    [unicode(release.id) for release in c.releases]
            },
            'contributions': {},
            'originals': {},
            'licenses': {},
            'relations': {},
            'content': {}
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
                    'mode': 'add',
                    'type': contribution.type,
                    'artist': contribution.artist.id
                })
            self.appstruct['contributions'] = {
                'contributions': _contributions
            }
        
        # original works, this creation is derived from
        if c.original_relations:
            _originals = []
            for original in c.original_relations:
                _originals.append(
                    {
                        'mode': 'edit',
                        'oid': original.oid,
                        'type': original.allocation_type,
                        'original': [{
                            'mode': 'edit', 
                            'code': original.derivative_creation.code,
                            'oid': original.derivative_creation.oid,
                            'titlefield': original.derivative_creation.title,
                            'artist': original.derivative_creation.artist.name
                        }]
                    }
                )
            self.appstruct['originals'] = {
                'originals': _originals
            }

        # content files that are assigned to the creation
        if c.content:
            _contentfiles = []
            for contentfile in c.content:
                _contentfiles.append(
                    {
                        'mode': 'add',
                        'oid': contentfile.oid,
                        'code': contentfile.code,
                        'name': contentfile.name,
                        'category': contentfile.category
                    }
                )
            self.appstruct['content'] = {
                'content': _contentfiles
            }

        # render form with init data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def update_creation(self):
        a = self.appstruct
        web_user = self.request.web_user
        creation = self.context.creation

        # (working)title
        if creation.title != a['metadata']['title']:
            creation.title = a['metadata']['title']

        # artist
        if creation.artist != a['metadata']['artist']:
            creation.artist = a['metadata']['artist']

        # # generate vlist
        # _creation = {
        #     'title': a['metadata']['title'],
        #     'artist': a['metadata']['artist'],
        #     'releases': a['metadata']['releases'],
        # }
        # 
        # # releases
        # if a['metadata']['releases']:
        #     _creation['releases'] = []
        #     for release_id in a['metadata']['releases']:
        #         _creation['releases'].append(
        #             (
        #                 'create',
        #                 [{
        #                     'release': release_id,
        #                     'title': a['metadata']['title'],
        #                     # TODO: manage different titles for releases
        #                     #       using a datatables control
        #                     # 'medium_number': TODO: medium_number
        #                     # 'track_number': TODO: track_number
        #                     # 'license ': TODO: license
        #                 }]
        #             )
        #         )

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
        
        # older version, merge rubbish? maybe can be deleted:
        # if a['relations']['original_creations']:
        #    _creation['original_relations'] = []
        #    for original_creation in a[
        #            'relations']['original_creations']:
        #        _creation['original_relations'].append(
        #            (
        #                'create',
        #                [{
        #                    'original_creation': original_creation['creation'],
        #                    'allocation_type': original_creation['type']
        #                }]
        #            )
        #        )
        # if a['relations']['derivative_creations']:
        #    _creation['derivative_relations'] = []
        #    for derivative_creation in a[
        #            'relations']['derivative_creations']:
        #        _creation['derivative_relations'].append(
        #            (
        #                'create',
        #                [{
        #                    'derivative_creation': derivative_creation[
        #                        'creation'
        #                    ],
        #                    'allocation_type': derivative_creation['type']
        #                }]
        #            )
        #        )

        #if a['content']['content']:
        #    _creation['content'] = []
        #    for contentlistenty in a['content']['content']:
        #        content = Content.search_by_oid(contentlistenty['oid'])
        #        if content:
        #            _creation['content'].append(
        #                (
        #                    'add',
        #                    [content.id]
        #                )
        #            )

        # the form data as in self.appstract (alias a) looks like this: 
        #
        # 'metadata': { ... },
        # 'originals': {
        #   'originals': [
        #       {
        #           'oid': '', 
        #           'type': u'cover', 
        #           'mode': u'create', 
        #           'original': [
        #               {
        #                   'code': u'C0000000003',
        #                   'oid': u'af69a047-6b77-4d04-ab54-ef4fae94cc08',
        #                   'titlefield': u'Working Title of Song 003',
        #                    'mode': u'add',
        #                   'artist': u'Solo Artist 001'
        #               }]
        #           }]
        #       },
        # 'content': { ... },
        # ...

        # look for removed originals
        # originals = CreationDerivative.search_originals_of_creation_by_id(
        #    creation.id)        
        originals = creation.original_relations
        oids_to_preserve = []
        for a_original in a['originals']['originals']:
            # sanity: already in list? then it must be a dupe: only add once
            if a_original['oid'] not in oids_to_preserve:
                oids_to_preserve.append(a_original['oid'])
        if originals:
            for original in originals:  # loop through database
                # original from db table no longer in appstruct?
                if original.oid not in oids_to_preserve:
                    CreationDerivative.delete([original])  # remove it from db

        # add new derivative-original relations or perform edits there
        # (objects starting with a_ relate to form data provided by appstruct)
        for a_original_relation in a['originals']['originals']:
            a_original = a_original_relation['original'][0]
            if a_original_relation['mode'] == 'create':
                # sanity checks
                if a_original['code'] == creation.code:  # original of self?
                    continue
                if a_original['mode'] == 'add':
                    original = Creation.search_by_oid(a_original['oid'])
                    if not original:
                        # TODO: Userfeedback
                        continue
                    _original = {
                        'original_creation': original.id,
                        'derivative_creation': creation.id,
                        'allocation_type': a_original_relation['type']
                    }
                    new_originals = CreationDerivative.create([_original])
                    if new_originals:
                        new_original = new_originals[0]
                if a_original['mode'] == 'create':
                    pass
            if a_original_relation['mode'] == 'edit':
                #import rpdb2; rpdb2.start_embedded_debugger("supersecret", fAllowRemote = True)

                # change the allocation_type, e.g. from 'remix' to 'cover'
                self.newmethod656(a_original_relation)

                if a_original['mode'] == 'add':
                    pass
                if a_original['mode'] == 'create':
                    pass
                if a_original['mode'] == 'edit':
                    pass
        
        # content
        contents_to_add = []
        for content_item in self.appstruct['content']['content']:
            content = Content.search_by_oid(content_item['oid'])
            if content:
                # content = Content.search_by_code(content_item['code'])
                # sanity checks
                # TODO: maybe something like this:
                # # is not the webusers content and wasn't there before?
                # if web_user.party != content.entity_creator:  # skip it!
                #     if content not in creation.content:
                #         self.request.session.flash(
                #             _(u"Content couldn't be added: ") + content.title,
                #             'main-alert-warning'
                #         )
                #         continue
                contents_to_add.append(content)
        creation.content = contents_to_add

        # # remove empty fields
        # for index, value in _creation.items():
        #     if not value:
        #         del _creation[index]

        # update creation
        creation.save()

        # user feedback
        log.info("creation edit successful for %s: %s" % (web_user, creation))
        self.request.session.flash(
            _(u"Creation edited: ") + creation.title
            + " ("+creation.code+")", 'main-alert-success'
        )

        # redirect
        self.redirect()

    def newmethod656(self, a_original_relation):
        relation = CreationDerivative.search_by_oid(
                a_original_relation['oid'])
        relation.allocation_type = a_original_relation['type']
        relation.save()


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Widgets -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

# --- Schemas -----------------------------------------------------------------

# --- Forms -------------------------------------------------------------------

def edit_creation_form(request):
    return deform.Form(
        schema=AddCreationSchema(
            validator=validate_content).bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
