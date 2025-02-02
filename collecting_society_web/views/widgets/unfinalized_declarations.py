# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from ...services import _
from ...models import Declaration


class UnfinalizedDeclarationsWidget():

    def __init__(self, request):
        self.unfinalized_declaration_codes = [{
                'code': declaration.code,
                'name': declaration.context.name,
            } for declaration in Declaration.search([
                ('active', '=', 'True'),
                ('licensee', '=', request.party),
                ('state', '=', 'submitted'),
                ('utilisations.state', '=', 'confirmed')
            ]) if declaration.next_step == 'finalization'
        ]

    def condition(self):
        return bool(self.unfinalized_declaration_codes)

    def icon(self):
        return "element-icon-declarations-yellow.svg"

    def badge(self):
        return len(self.unfinalized_declaration_codes)

    def header(self):
        return _("Unfinalized Declarations")

    def description(self):
        return _("Please finalize your Declarations:")

    def links(self):
        return [{
            'name': declaration['name'],
            'path': ['licensing', 'declarations',
                     declaration['code'], 'finalize'],
        } for declaration in self.unfinalized_declaration_codes]

    def buttons(self):
        return False
