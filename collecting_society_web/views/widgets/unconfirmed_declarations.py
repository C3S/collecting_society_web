# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from ...services import _
from ...models import Declaration


class UnconfirmedDeclarationsWidget():

    def __init__(self, request):
        self.unconfirmed_declaration_codes = [{
                'code': declaration.code,
                'name': declaration.context.name,
            } for declaration in Declaration.search([
                ('active', '=', 'True'),
                ('licensee', '=', request.party),
                ('state', '=', 'submitted'),
                ('utilisations.state', '=', 'estimated')
            ]) if declaration.next_step == 'confirmation'
        ]

    def condition(self):
        return bool(self.unconfirmed_declaration_codes)

    def icon(self):
        return "element-icon-declarations-yellow.svg"

    def badge(self):
        return len(self.unconfirmed_declaration_codes)

    def header(self):
        return _("Unconfirmed Declarations")

    def description(self):
        return _("Please confirm your Declarations:")

    def links(self):
        return [{
            'name': declaration['name'],
            'path': ['licensing', 'declarations',
                     declaration['code'], 'confirm'],
        } for declaration in self.unconfirmed_declaration_codes]

    def buttons(self):
        return False
