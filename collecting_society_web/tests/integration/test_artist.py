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
from ...views.forms.edit_artist import (
    edit_artist_form
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
        browser.screenshot("navigated_to_add_artist")

    @Tdb.transaction()
    def test_020_create_artist(self, browser, request_with_registry):
        """
        add an artist
        """
        # browser.get("/repertoire/artists/add")

        formid = 'AddArtist'
        form = DeformFormObject(
            browser, add_artist_form(request_with_registry), formid)
        form.group.set(False)
        form.name.set("Testartist #12345")
        form.ipn_code.set("12345678901")
        form.description.set("This is example of a solo artist.")
        # TODO: test picture upload
        # TODO: test group artist
        form.submit()
        assert browser.find_element(By.CLASS_NAME, "alert-success")

        assert "Testartist #12345" in browser.page_source  # check for name,
        assert "This is example of a solo artist." in browser.page_source
        assert "12345678901" in browser.page_source  # IPN, and description

    def test_025_click_edit_artist(self, browser):
        browser.find_element(By.CLASS_NAME, "btn-artist-edit").click()
        assert "/artists/" in browser.current_url
        assert browser.current_url.endswith("/edit")
        browser.screenshot("navigated_to_edit_artist")

    @Tdb.transaction()
    def test_030_edit_artist(self, browser, request_with_registry):
        """
        edit an artist
        """
        # import debugpy
        # debugpy.listen(("0.0.0.0", 52003))
        # debugpy.wait_for_client()
        # breakpoint()
        formid = 'EditArtist'
        form = DeformFormObject(
            browser, edit_artist_form(request_with_registry), formid)
        form.name.set("Testartist #54321")
        form.ipn_code.set("98765432101")
        form.description.set("This is *an* example of a solo artist.")
        # TODO: test picture upload
        # TODO: test group artist
        form.submit()

        assert browser.find_element(By.CLASS_NAME, "alert-success")

        assert "Testartist #12345" not in browser.page_source  # negative check
        assert "This is example of a solo artist." not in browser.page_source
        assert "12345678901" not in browser.page_source  # should not occur

        assert "Testartist #54321" in browser.page_source  # changed name,
        assert "This is *an* example of a solo artist." in browser.page_source
        assert "98765432101" in browser.page_source  # IPN, and description?

    @Tdb.transaction()
    def test_040_delete_artist(self, browser, request_with_registry):
        """
        delete an artist
        """
        browser.find_element(By.CLASS_NAME, "btn-artist-delete").click()
        assert browser.find_element(By.CLASS_NAME, "alert-success")
        # assert browser.current_url[-20:] == "/repertoire/artists/"
        # assert "Testartist #12345" not in browser.page_source
        browser.screenshot("clicked_artist_delete")

    def test_050_logout(self, browser):
        """
        log user out
        """
        browser.get("/logout")
        assert browser.find_elements(By.CLASS_NAME, 'cs-frontend')
