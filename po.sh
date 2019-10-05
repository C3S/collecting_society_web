pot-create -o collecting_society_web/locale/collecting_society_web.pot collecting_society_web
msgmerge --update collecting_society_web/locale/*/LC_MESSAGES/collecting_society_web.po collecting_society_web/locale/collecting_society_web.pot
poedit collecting_society_web/locale/de/LC_MESSAGES/collecting_society_web.po
msgfmt -o collecting_society_web/locale/de/LC_MESSAGES/collecting_society_web.mo collecting_society_web/locale/de/LC_MESSAGES/collecting_society_web.po
echo "You might want to restart the portal container now in order to see the new translations."
