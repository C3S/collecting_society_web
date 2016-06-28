collecting_society.portal.repertoire
====================================

Plugin for `Web Portal <https://github.com/C3S/collecting_society.portal>`_.

For a working development setup, see https://github.com/C3S/c3s.ado.repertoire

Translations
------------

Explanation
```````````
- **.pot**: "Portable Object Template" file, list of message identifiers, template for **.po** files
- **.po**: "Portable Object" file, human editable list of translated messages
- **.mo**: "Machine Object" file, machine readable list of messages, created from a **.po** file

Installation
````````````
- **poedit**: ``$apt-get install poedit``
- **gettext**: ``$apt-get install gettext``
- **lingua**: ``$pip install lingua``

**Note**: If you are running different python versions on the host, you need to ensure, that the right ``pip`` (e.g. ``pip2.7``) is called.

Updates
```````

e.g. for project **collecting_society.portal.imp** and language **de**

- only once, to start translation of a project, create the **.pot** file for the project
    - ``$cd c3s.ado.repertoire/ado/src/collecting_society.portal.repertoire``
    - ``$mkdir collecting_society_portal_repertoire/locale``
    - ``$pot-create -o collecting_society_portal_repertoire/locale/collecting_society_portal_repertoire.pot collecting_society_portal_repertoire``
- only once, if you need a new language, create the **.po** file for the language
    - ``$cd c3s.ado.repertoire/ado/src/collecting_society.portal.repertoire/collecting_society_portal_repertoire/locale``
    - ``$mkdir -p de/LC_MESSAGES``
    - ``$msginit -l de -o de/LC_MESSAGES/collecting_society_portal_repertoire.po``
- each time, the code or templates changed, recreate the **.pot** file:
    - ``$cd c3s.ado.repertoire/ado/src/collecting_society.portal.repertoire``
    - ``$pot-create -o collecting_society_portal_repertoire/locale/collecting_society_portal_repertoire.pot collecting_society_portal_repertoire``
- every time the **.pot** file changed, recreate the **.po** files for all languages
    - ``$cd c3s.ado.repertoire/ado/src/collecting_society.portal.repertoire``
    - ``$msgmerge --update collecting_society_portal_repertoire/locale/*/LC_MESSAGES/collecting_society_portal_repertoire.po collecting_society_portal_repertoire/locale/collecting_society_portal_repertoire.pot``
- to edit translations, change the **.po** file via poedit
    - ``$cd c3s.ado.repertoire/ado/src/collecting_society.portal.repertoire``
    - ``$poedit collecting_society_portal_repertoire/locale/de/LC_MESSAGES/collecting_society_portal_repertoire.po``
- every time the **.po** file changed, create a **.mo** file
    - ``$cd c3s.ado.repertoire/ado/src/collecting_society.portal.repertoire``
    - ``$msgfmt -o collecting_society_portal_repertoire/locale/de/LC_MESSAGES/collecting_society_portal_repertoire.mo collecting_society_portal_repertoire/locale/de/LC_MESSAGES/collecting_society_portal_repertoire.po``

Further information
```````````````````

- see `pyramid documentation <http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/i18n.html#working-with-gettext-translation-files>`_


Copyright / License
-------------------

For infos on copyright and licenses, see ``./COPYRIGHT.rst``
