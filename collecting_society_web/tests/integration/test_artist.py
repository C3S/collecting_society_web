# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

import pytest

from selenium.webdriver.common.by import By

from portal_web.tests.integration.pageobjects import DeformFormObject
from portal_web.views.forms.login_web_user import login_form
from portal_web.models import Tdb

from ...views.forms.add_artist import (
    add_artist_form
)


@pytest.fixture(autouse=True, scope='class')
def web_user(create_web_user):
    create_web_user(
        email='licenser@username.test',
        password='password',
        opt_in_state='opted-in',
    )


class TestArtist:
    """
    Artist management scenario.
    """

    def test_010_login_licenser(self, browser):
        """
        login licenser
        """
        browser.get("/")
        formid = 'LoginWebuser'
        form = DeformFormObject(browser, login_form(), formid)
        form.login_email.set('licenser@username.test')
        form.login_password.set('password')
        form.submit()
        assert browser.find_elements(By.CLASS_NAME, 'cs-backend')

    def test_012_navigate_to_repertoire(self, browser):
        browser.find_element(By.CLASS_NAME, "cs-menue-item-repertoire").click()
        assert browser.find_element(By.CLASS_NAME, "introtext")

    def test_014_navigate_to_artist(self, browser):
        browser.find_element(By.CLASS_NAME, "cs-menue-item-artists").click()
        assert browser.current_url[-20:] == "/repertoire/artists/"

    def test_016_click_add_artist(self, browser):
        browser.find_element(By.CLASS_NAME, "btn-artist-add").click()
        assert browser.current_url[-23:] == "/repertoire/artists/add"

    @Tdb.transaction()
    def test_020_create_artist(self, browser, request_with_registry):
        """
        add an artist
        """
        browser.get("/repertoire/artists/add")
        browser.screenshot("navigated_to_artist_add")

        formid = 'AddArtist'
        form = DeformFormObject(
            browser, add_artist_form(request_with_registry), formid)
        form.group.set(False)
        form.name.set('Testartist #12345')
        # form.ipn_code.set('1970-01-01')
        # form.register_email.set('a@webuser.test')
        # form.register_password.set('awebuser')
        # form.terms_accepted.set(True)
        # form.register_webuser()
        form.submit()
        assert browser.find_element(By.CLASS_NAME, "alert-success")
