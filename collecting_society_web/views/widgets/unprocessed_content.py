# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from ...models import Content
from portal_web.models import WebUser

from ...services import _


class UnprocessedContentWidget():

    def __init__(self, request, category='all'):
        party = WebUser.current_web_user(request).party
        content_count = Content.search_unprocessed(party, category)
        self.content_count = content_count and len(content_count) or 0
        self.category = category

    def condition(self):
        return self.content_count

    def icon(self):
        return "glyphicon glyphicon-plus-sign"

    def header(self):
        return _("Unprocessed Files")

    def description(self):
        return _("Number of files that are enqueued for processing by our "
                 "servers. There is nothing you can do but wait. Processing "
                 "can take anything from under a minute to several hours "
                 "depending on server loads. Please come back later to see "
                 "if we are finished processing your files.")

    def badge(self):
        return self.content_count
