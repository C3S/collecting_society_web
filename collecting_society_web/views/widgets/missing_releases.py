# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from ...models import Artist, Content, Creation, Release

from ...services import _


class MissingReleasesWidget():

    def __init__(self, request, category='all'):
        content_count = Content.current_viewable(request)
        artist_count = Artist.current_editable(request)
        creation_count = Creation.current_viewable(request)
        release_count = Release.current_viewable(request)
        self.artist_count = artist_count and len(artist_count) or 0
        self.content_count = content_count and len(content_count) or 0
        self.creation_count = creation_count and len(creation_count) or 0
        self.release_count = release_count and len(release_count) or 0
        self.category = category

    def condition(self):
        # only show if artists, content files, and creations have already
        # been created but releases haven't been created yet
        return (self.artist_count > 0 and self.content_count > 0 and
                self.creation_count > 0 and self.release_count == 0)

    def icon(self):
        return "glyphicon glyphicon-cd"

    def header(self):
        return _(u"Missing Releases")

    def description(self):
        return _(u"You didn't create any releases yet. Please do so using the "
                 "menu on the left side. Releases are generally collections "
                 "of creations that have been made available to the public. "
                 "Sometimes only one creation is part of a release (called a "
                 "'single'). Creations are organized on a release using track "
                 "numbers and medium numbers. Note that you may use "
                 "track titles that differ from the genuine creation title.")

    def badge(self):
        return self.release_count
