# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from ...models import Artist

from ...services import _


class MissingArtistsWidget():

    def __init__(self, request, category='all'):
        self.party = request.party.id
        self.category = category

    def condition(self):
        return self.badge() == 0

    def icon(self):
        return "glyphicon glyphicon-user"

    def header(self):
        return _(u"Missing Artists")

    def description(self):
        return _(u"You didn't create any artists yet. Please do so using the "
                 "menu on the left side. There are two types of artists: solo "
                 "and group artists. A solo artist can be identical to your "
                 "birth name, a stage name, project name, or any sort of "
                 "pseudonym you "
                 "associate the works of your solo career with. The solo "
                 "artist is also used to document the role you played as part "
                 "of a collective effort while creating a song. "
                 "A group artist, on the other side, is any form of "
                 "association of individual artists in order to create "
                 "musical works, for example a band or a collaboration. "
                 "When creating a group artist, you will be asked to add "
                 "solo artists as members, so it's a good idea to create "
                 "your own solo artist(s) first. 'Foreign' artists, for "
                 "example "
                 "band members, that refer to other persons, can be created "
                 "'on the fly' using the member create button in the group "
                 "artist creation form. To create a group artist, go to the "
                 "create artist form and make a check below 'Group'.")

    def get_len(self, content_list):
        if content_list:
            return len(content_list)
        else:
            return 0

    def badge(self):
        return self.get_len(Artist.search_by_party(self.party))
