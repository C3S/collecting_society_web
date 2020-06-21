# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import os
import logging

from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import (
    view_config,
    view_defaults
)

from portal_web.models import Tdb
from portal_web.views import ViewBase

from ..services import _
from ..models import Location
from .forms import (
    AddLocation,
    EditLocation
)

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.LocationsResource')
class LocationsViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/location/list.pt',
        permission='list_locations')
    def list(self):
        return {}

    @view_config(
        name='add',
        renderer='../templates/location/add.pt',
        permission='add_location')
    def add(self):
        self.register_form(AddLocation)
        return self.process_forms()


@view_defaults(
    context='..resources.LocationResource')
class LocationViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/location/show.pt',
        permission='show_location')
    def show(self):
        return {}

    @view_config(
        name='edit',
        renderer='../templates/location/edit.pt',
        permission='edit_location')
    def edit(self):
        self.register_form(EditLocation)
        return self.process_forms()

    @view_config(
        name='delete',
        permission='delete_location',
        decorator=Tdb.transaction(readonly=False))
    def delete(self):
        # TODO: check if location is used in any event and disallow delete then
        name = self.context.location.name
        Location.delete([self.context.location])
        log.info("location delete successful for %s: %s (%s)" % (
            self.request.web_user, name, self.context.code
        ))
        self.request.session.flash(
            _(u"Location deleted: ") + name,
            _(u"Location deleted: ${name}",
              mapping={'name': name}),
            'main-alert-success'
        )
        return self.redirect('..')
