# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import os

from pyramid.renderers import render

from ...services import _


class ServiceInfoWidget():

    def __init__(self, request):
        self.template = '../../templates/widgets/service_info.pt'
        self.branch = os.environ.get("BRANCH")
        self.environment = os.environ.get("ENVIRONMENT")
        self.build = os.environ.get("BUILD")

    def title(self):
        return _("Portal")

    def subtitle(self):
        if self.branch == "production":
            return False
        return self.branch

    def subtitle_note(self):
        if self.branch == "production":
            return False
        if self.branch == "staging":
            return "build %s" % self.build
        return "environment: %s" % self.environment

    def description(self):
        return _(
            "Welcome on the user portal of C3S. This service enables "
            "licensers to register their artists, creations and releases, and "
            "licensees to register their utilisations.")

    def render(self):
        return render(
            self.template, {
                'title': self.title(),
                'subtitle': self.subtitle(),
                'subtitle_note': self.subtitle_note(),
                'description': self.description(),
            })
