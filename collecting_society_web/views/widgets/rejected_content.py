# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from ...models import Content
from ...services import _

rejection_reasons = {
    'checksum_collision': _('Duplicate Checksum'),
    'fingerprint_collision': _('Duplicate Fingerprint'),
    'format_error': _('Format Error'),
    'no_fingerprint': _('No Fingerprint'),
    'lossy_compression': _('Lossy Compression'),
    'missing_database_record': _('Missing Database Record'),
}


class RejectedContentWidget():

    def __init__(self, request, category='all'):
        self.rejected_content = [{
                'name': content.name,
                'code': content.code,
                'reason': rejection_reasons.get(content.rejection_reason, ''),
            } for content in Content.search_rejects(
                party_id=request.party,
            )
        ]
        self.category = category

    def condition(self):
        return bool(self.rejected_content)

    def icon(self):
        return "glyphicon-ban-circle"

    def header(self):
        return _("Rejected Content")

    def description(self):
        return _("Total number of files you uploaded that where rejected")

    def links(self):
        return [{
            'name': f"{content['name']} ({content['reason']})",
            'path': ['repertoire', 'files', content['code']],
        } for content in self.rejected_content]

    def badge(self):
        return len(self.rejected_content)
