# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import colander
import deform
from pkg_resources import resource_filename
import logging

from pyramid.threadlocal import get_current_request
from pyramid.i18n import get_localizer

from collecting_society_portal.models import (
    Tdb,
    WebUser
)
from collecting_society_portal.views.forms import (
    FormController,
    deferred_file_upload_widget
)
from ...services import _
from ...models import (
    Artist,
    Creation,
    Genre,
    Label,
    License,
    Party,
    Release
)
from ...resources import ReleaseResource
from .add_release import add_release_form

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class EditRelease(FormController):
    """
    form controller for edit release
    """

    def controller(self):
        code = self.context.release_code
        if code is None:
            self.request.session.flash(
                _(u"Could not edit release - code is missing"),
                'main-alert-warning'
            )
            return self.redirect(ReleaseResource, 'list')
        self.release = Release.search_by_code(code)
        if self.release is None:
            self.request.session.flash(
                _(u"Could not edit release - release not found"),
                'main-alert-warning'
            )
            return self.redirect(ReleaseResource, 'list')        
        self.context.release_code = code

        self.form = add_release_form(self.request) # lend schemas from add_release

        if not (self.submitted() and self.validate()):
            self.load_release()                    
            self.render(self.appstruct)
            self.response.update({'release': self.release}) # attach to display image in template
        else:  
            # submit validated data from form            
            self.save_release()

        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=True)
    def load_release(self):

        # tab superstructure
        self.appstruct = {
            'general': {},
            'production': {},
            'distribution': {},
            'genres': {}
        }

        # initialize form
        tab = 'general'
        def set_formdata(value):    # a little embedded helper function
            self.appstruct[tab][value] = getattr(self.release, value) or ""
        set_formdata('title')
        set_formdata('number_mediums')
        set_formdata('ean_upc_code')
        set_formdata('isrc_code')
        set_formdata('warning')
        # production tab
        tab = 'production'
        set_formdata('copyright_date')
        set_formdata('production_date')
        set_formdata('producer')
        # distribution tab
        tab = 'distribution'
        self.appstruct['distribution']['label'] = self.release.label.gvl_code
        set_formdata('label_catalog_number')
        set_formdata('release_date')
        set_formdata('release_cancellation_date')
        set_formdata('online_release_date')
        set_formdata('online_cancellation_date')
        set_formdata('distribution_territory')
        set_formdata('neighbouring_rights_society')
        # genres tab
        self.appstruct['genres']['genres'] = [unicode(genre.id) for genre in 
            self.release.genres]

    @Tdb.transaction(readonly=False)
    def save_release(self):
        log.debug(
            (
                "self.appstruct: %s\n"
            ) % (
                self.appstruct
            )
        )
  
        # general tab
        tab = 'general'
        def get_formdata(value):    # a little embedded helper function
            if self.appstruct[tab][value]:
                setattr(self.release, value, self.appstruct[tab][value])
        get_formdata('title')
        get_formdata('number_mediums')
        get_formdata('ean_upc_code')
        get_formdata('isrc_code')
        get_formdata('warning')
        if self.appstruct['general']['picture']:
            with open(self.appstruct['general']['picture']['fp'].name,
                      mode='rb') as picfile:
                picture_data = picfile.read()
            mimetype = self.appstruct['general']['picture']['mimetype']
            self.release.picture_data = picture_data
            self.release.picture_data_mime_type = mimetype
        # production tab
        tab = 'production'
        get_formdata('copyright_date')
        get_formdata('production_date')
        get_formdata('producer')
        # distribution tab
        tab = 'distribution'
        if self.appstruct['distribution']['label']:
            label = Label.search_by_gvl_code(
                self.appstruct['distribution']['label'])
            if label:
                self.release.label = label
        get_formdata('label_catalog_number')
        get_formdata('release_date')
        get_formdata('release_cancellation_date')
        get_formdata('online_release_date')
        get_formdata('online_cancellation_date')
        get_formdata('distribution_territory')
        get_formdata('neighbouring_rights_society')
        # genres tab
        if self.appstruct['genres']['genres']:
            self.release.genres = self.appstruct['genres']['genres']

        self.release.save()

        self.redirect(ReleaseResource, 'list')

# --- Validators --------------------------------------------------------------

# --- Options -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

# --> gets Schemas from add_release.py!