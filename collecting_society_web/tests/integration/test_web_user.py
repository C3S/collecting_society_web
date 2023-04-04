# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from selenium.webdriver.common.by import By

from portal_web.tests.integration.pageobjects import DeformFormObject
from portal_web.views.forms.login_web_user import login_form
from portal_web.models import Tdb, WebUser

from ...views.forms.register_webuser import (
    claims_membership_form,
    register_nonmember_form
)


class TestWebUser:
    """
    User registration scenario.
    """
    def test_010_registration(self, browser):
        """
        registration registers user
        """
        browser.delete_all_cookies()
        browser.get("/")
        formid = 'RegisterWebuser'
        form = DeformFormObject(browser, claims_membership_form(), formid)
        form.claims_membership()
        form = DeformFormObject(browser, register_nonmember_form(), formid)
        form.firstname.set('Firstname')
        form.lastname.set('Lastname')
        form.birthdate.set('1970-01-01')
        form.register_email.set('a@webuser.test')
        form.register_password.set('awebuser')
        form.terms_accepted.set(True)
        form.register_webuser()
        assert "Thank you for your registration" in browser.page_source

    def test_020_login_before_validation(self, browser):
        """
        login before validation fails
        """
        formid = 'LoginWebuser'
        form = DeformFormObject(browser, login_form(), formid)
        form.login_email.set('a@webuser.test')
        form.login_password.set('awebuser')
        form.submit()
        assert "User mail address not verified" in browser.page_source

    @Tdb.transaction()
    def test_030_validate_user_registration(self, browser):
        """
        validate user registration succeeds and logs user in
        """
        webuser = WebUser.search_by_email('a@webuser.test')
        assert webuser.opt_in_state == "mail-sent"
        browser.get("/verify_email/" + webuser.opt_in_uuid)
        assert browser.find_elements(By.CLASS_NAME, 'cs-backend')

    def test_040_logout(self, browser):
        """
        logout logs user out
        """
        browser.get("/logout")
        assert browser.find_elements(By.CLASS_NAME, 'cs-frontend')

    def test_050_login_with_wrong_credentials(self, browser):
        """
        login with wrong credentials fails
        """
        formid = 'LoginWebuser'
        form = DeformFormObject(browser, login_form(), formid)
        form.login_email.set('a@webuser.test')
        form.login_password.set('wrongpassword')
        form.submit()
        assert "Login failed" in browser.page_source

    def test_060_login_with_right_credentials(self, browser):
        """
        login with right credentials logs user in
        """
        formid = 'LoginWebuser'
        form = DeformFormObject(browser, login_form(), formid)
        form.login_email.set('a@webuser.test')
        form.login_password.set('awebuser')
        form.submit()
        assert browser.find_elements(By.CLASS_NAME, 'cs-backend')

    def _test_070_check_locale(self, browser):
        formid = 'LoginWebuser'
        form = DeformFormObject(browser, login_form(), formid)
        en, de = browser.find_elements(By.CLASS_NAME, "cs-langflags")

        en.click()
        browser.screenshot('en')
        assert browser.get_cookie("_LOCALE_") == "en"

        de.click()
        browser.screenshot('de')
        assert browser.get_cookie("_LOCALE_") == "de"
        assert form._form.buttons[0].title == 'Übernehmen'

        en.click()
        browser.screenshot('en')
        assert browser.get_cookie("_LOCALE_") == "en"
        assert form._form.buttons[0].title == 'Submit'
