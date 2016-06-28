# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

import os

import logging

from pyramid.renderers import render
from pyramid.response import FileResponse
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import (
    view_config,
    view_defaults
)

from collecting_society_portal.resources import (
    FrontendResource,
    BackendResource
)
from collecting_society_portal.views import ViewBase
from collecting_society_portal.views.forms import (
    LoginWebuser
)

from .forms import RegisterWebuser

log = logging.getLogger(__name__)


@view_defaults(
    context=FrontendResource,
    permission=NO_PERMISSION_REQUIRED)
class PagePortalViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/page/home.pt')
    def home(self):
        self.register_form(LoginWebuser)
        self.register_form(RegisterWebuser)
        return self.process_forms()
