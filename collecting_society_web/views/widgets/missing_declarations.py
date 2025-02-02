# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from ...services import _
from ...models import Declaration


class MissingDeclarationsWidget():

    def __init__(self, request):
        self.has_declarations = bool(
            Declaration.search_viewable_by_web_user(request.web_user.id))

    def condition(self):
        return not self.has_declarations

    def icon(self):
        return "element-icon-declarations-yellow.svg"

    def header(self):
        return _("Missing Declaration")

    def description(self):
        return _("Please add your first Declaration")

    def buttons(self):
        return [{
            'name': _('Add Declaration'),
            'path': ['licensing', 'declarations', 'add'],
        }]

    def badge(self):
        return False
