collecting_society_web
======================

Plugin for `portal_web <https://github.com/C3S/portal_web>`_ 
including:

- Artists
- Creations
- Contents
- Releases

For a working development setup, see https://github.com/C3S/collecting_society_docker

Artists
-------

Enables web users to manage group and solo artists.


Creations
---------

Enables web users to upload and manage creations, define licenses and relations
to other artists and creations.

Contents
--------

Audio files associated with creations.


Releases
--------

A group of creations bound together on a medium.

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

e.g. for project **collecting_society_web** and language **de**

- only once, to start translation of a project, create the **.pot** file for the project
    - ``$cd collecting_society_docker/volumes/shared/src/collecting_society_web``
    - ``$mkdir collecting_society_web/locale``
    - ``$pot-create -o collecting_society_web/locale/collecting_society_web.pot collecting_society_web``
- only once, if you need a new language, create the **.po** file for the language
    - ``$cd collecting_society_docker/volumes/shared/src/collecting_society_web/collecting_society_web/locale``
    - ``$mkdir -p de/LC_MESSAGES``
    - ``$msginit -l de -o de/LC_MESSAGES/collecting_society_web.po``
- each time, the code or templates changed, recreate the **.pot** file:
    - ``$cd collecting_society_docker/volumes/shared/src/collecting_society_web``
    - ``$pot-create -o collecting_society_web/locale/collecting_society_web.pot collecting_society_web``
- every time the **.pot** file changed, recreate the **.po** files for all languages
    - ``$cd collecting_society_docker/volumes/shared/src/collecting_society_web``
    - ``$msgmerge --update collecting_society_web/locale/*/LC_MESSAGES/collecting_society_web.po collecting_society_web/locale/collecting_society_web.pot``
- to edit translations, change the **.po** file via poedit
    - ``$cd collecting_society_docker/volumes/shared/src/collecting_society_web``
    - ``$poedit collecting_society_web/locale/de/LC_MESSAGES/collecting_society_web.po``
- every time the **.po** file changed, create a **.mo** file
    - ``$cd collecting_society_docker/volumes/shared/src/collecting_society_web``
    - ``$msgfmt -o collecting_society_web/locale/de/LC_MESSAGES/collecting_society_web.mo collecting_society_web/locale/de/LC_MESSAGES/collecting_society_web.po``

Further information
```````````````````

- see `pyramid documentation <http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/i18n.html#working-with-gettext-translation-files>`_


Copyright / License
-------------------

For infos on copyright and licenses, see ``./COPYRIGHT.rst``
