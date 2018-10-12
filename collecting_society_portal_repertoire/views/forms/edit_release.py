# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import logging
import deform

from collecting_society_portal.models import Tdb
from collecting_society_portal.views.forms import FormController

from ...services import _
from ...models import Label
from ...resources import ReleaseResource
from .add_release import AddReleaseSchema

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class EditRelease(FormController):
    """
    form controller for edit release
    """

    def controller(self):
        self.form = edit_release_form(self.request)
        if self.submitted():
            if self.validate():
                self.update_release()
        else:
            self.edit_release()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=True)
    def edit_release(self):
        r = self.context.release

        # set appstruct
        self.appstruct = {
            'general': {
                'title':
                    r.title or '',
                'number_mediums':
                    r.number_mediums or '',
                'ean_upc_code':
                    r.ean_upc_code or '',
                'isrc_code':
                    r.isrc_code or '',
                'warning':
                    r.warning or '',
            },
            'label': {
                'label_catalog_number':
                    r.label_catalog_number or '',
            },
            'production': {
                'copyright_date':
                    r.copyright_date or '',
                'production_date':
                    r.production_date or '',
                'producer':
                    r.producer or '',
            },
            'distribution': {
                'release_date':
                    r.release_date or '',
                'release_cancellation_date':
                    r.release_cancellation_date or '',
                'online_release_date':
                    r.online_release_date or '',
                'online_cancellation_date':
                    r.online_cancellation_date or '',
                'distribution_territory':
                    r.distribution_territory or '',
                'neighbouring_rights_society':
                    r.neighbouring_rights_society or '',
            },
            'genres': {
                'genres':
                    [unicode(genre.id) for genre in r.genres],
                'styles':
                    [unicode(style.id) for style in r.styles],
            }
        }

        # set label
        if r.label:
            self.appstruct['label']['label'] = [{
                'mode': 'add',
                'name': r.label.name,
                'gvl_code': r.label.gvl_code,
            }]
        elif r.label_name:
            self.appstruct['label']['label'] = [{
                'mode': 'edit',
                'name': r.label_name,
                'gvl_code': '',
            }]

        # render form with data
        self.render(self.appstruct)

    @Tdb.transaction(readonly=False)
    def update_release(self):
        a = self.appstruct
        email = self.request.unauthenticated_userid
        release = self.context.release

        # generate vlist
        _release = {
            'title':
                a['general']['title'],
            'number_mediums':
                a['general']['number_mediums'],
            'ean_upc_code':
                a['general']['ean_upc_code'],
            'isrc_code':
                a['general']['isrc_code'],
            'warning':
                a['general']['warning'],
            'label_catalog_number':
                a['label']['label_catalog_number'],
            'copyright_date':
                a['production']['copyright_date'],
            'production_date':
                a['production']['production_date'],
            'producer':
                a['production']['producer'],
            'release_date':
                a['distribution']['release_date'],
            'release_cancellation_date':
                a['distribution']['release_cancellation_date'],
            'online_release_date':
                a['distribution']['online_release_date'],
            'online_cancellation_date':
                a['distribution']['online_cancellation_date'],
            'distribution_territory':
                a['distribution']['distribution_territory'],
            'neighbouring_rights_society':
                a['distribution']['neighbouring_rights_society'],
            'genres':
                [('add', map(int, a['genres']['genres']))],
            'styles':
                [('add', map(int, a['genres']['styles']))],
        }

        # label
        _label = a['label']['label'] and a['label']['label'][0]
        if not _label:
            release.label_name = None
            release.label = None
            release.save()
        else:
            if _label['mode'] == "add":
                label = Label.search_by_gvl_code(_label['gvl_code'])
                if label:
                    release.label_name = None
                    release.label = label.id
                    release.save()
            if _label['mode'] in ["create", "edit"]:
                release.label_name = _label['name']
                release.label = None
                release.save()

        # picture
        if a['general']['picture']:
            with open(a['general']['picture']['fp'].name,
                      mode='rb') as picfile:
                picture_data = picfile.read()
            mimetype = a['general']['picture']['mimetype']
            _release['picture_data'] = picture_data
            _release['picture_data_mime_type'] = mimetype

        # remove empty fields
        for index, value in _release.items():
            if not value:
                del _release[index]

        # update release
        release.write([release], _release)

        # user feedback
        log.info("edit release successful for %s: %s" % (email, release))
        self.request.session.flash(
            _(u"Release edited: ") + release.title + " (" + release.code + ")",
            'main-alert-success'
        )

        # redirect
        self.redirect(ReleaseResource, 'list')


# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

# --- Schemas -----------------------------------------------------------------

# --- Forms -------------------------------------------------------------------

def edit_release_form(request):
    return deform.Form(
        schema=AddReleaseSchema(
            title=_(u"Edit Release")
        ).bind(request=request),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
