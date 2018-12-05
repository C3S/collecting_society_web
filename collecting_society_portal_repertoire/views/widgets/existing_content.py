# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

from pyramid.renderers import render

from ...models import Artist, Content

from ...services import _


class ExistingContentWidget():

    def __init__(self, request, category='all'):
        self.request = request
        self.party = request.party.id
        self.category = category

    def condition(self):
        # only show if artists have already be created
        number_of_artists = self.get_len(Artist.search_by_party(self.party))
        # artists there but nothing uploaded yet? show task
        number_of_content_files = self.badge()
        return number_of_artists > 0 and number_of_content_files == 0

    def icon(self):
        return "glyphicon glyphicon-plus-sign"

    def header(self):
        return _(u"Existing Files")

    def description(self):
        return _(u"You didn't upload any files yet. Please do so using the "
                 "menu on the left side. There are two types of files: audio "
                 "and pdf. PDFs should contain any form of sheet music, for "
                 "example exports from music notation software like MuseScore "
                 "or Noteflight, or even scans from handwritten scores. Audio "
                 "files have to be provided in a lossless format like .wav or "
                 ".flac -- lossy formats like .mp3 or .ogg will be rejected. "
                 "The reason we want to have this digital representation of "
                 "your work is that we can identify a song without doubt "
                 "should there be a dispute of sorts. We prefer audio files "
                 "because it allows us to track your works usage (and pay "
                 "your revenues) more directly. Start with one of the two "
                 "file types in order to associate it with a creation. You "
                 "may add a file of the other type later on.")

    def get_len(self, content_list):
        if content_list:
            return len(content_list)
        else:
            return 0

    def output(self):
        """
        not needed ?
        """
        return ""

    def badge(self):
        return self.get_len(Content.current_viewable(self.request))