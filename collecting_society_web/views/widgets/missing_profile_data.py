# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from ...services import _


class MissingProfileDataWidget():

    def __init__(self, request):
        self.has_address = bool(request.party.addresses)

    def condition(self):
        return not self.has_address

    def icon(self):
        return "glyphicon glyphicon-cog"

    def header(self):
        return _("Missing Profile Data")

    def description(self):
        return _("Please add your address in your Profile to be able to "
                 "receive invoices or royalties.")

    def links(self):
        return [{
            'name': _('Edit Profile'),
            'path': ['profile', 'edit'],
        }]

    def badge(self):
        return False
