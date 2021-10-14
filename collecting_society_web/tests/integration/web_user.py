# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_web

from selenium.webdriver.common.by import By

from portal_web.tests.base import (
    IntegrationTestBase,
    DeformFormObject
)

from portal_web.views.forms.login_web_user import login_form
from portal_web.models import Tdb, WebUser

from ...views.forms.register_webuser import (
    claims_membership_form,
    register_nonmember_form
)


class TestWebUser(IntegrationTestBase):

    def test_010_registration(self):
        """
        registration registers user
        """
        self.url("gui", "/")
        formid = 'RegisterWebuser'
        form = DeformFormObject(self, claims_membership_form(), formid)
        form.claims_membership()
        form = DeformFormObject(self, register_nonmember_form(), formid)
        form.firstname.set('Firstname')
        form.lastname.set('Lastname')
        form.birthdate.set('1970-01-01')
        form.register_email.set('a@webuser.test')
        form.register_password.set('awebuser')
        form.terms_accepted.set(True)
        form.register_webuser()
        self.assertIn("Thank you for your registration", self.cli.page_source)

    def test_020_login_before_validation(self):
        """
        login before validation fails
        """
        formid = 'LoginWebuser'
        form = DeformFormObject(self, login_form(), formid)
        form.login_email.set('a@webuser.test')
        form.login_password.set('awebuser')
        form.submit()
        self.assertIn("User mail address not verified", self.cli.page_source)

    @Tdb.transaction()
    def test_030_validate_user_registration(self):
        """
        validate user registration succeeds and logs user in
        """
        webuser = WebUser.search_by_email('a@webuser.test')
        self.assertEqual(webuser.opt_in_state, "mail-sent")
        self.url("gui", "/verify_email/" + webuser.opt_in_uuid)
        self.assertTrue(self.cli.find_elements(By.CLASS_NAME, 'cs-backend'))

    def test_040_logout(self):
        """
        logout logs user out
        """
        self.url("gui", "/logout")
        self.assertTrue(self.cli.find_elements(By.CLASS_NAME, 'cs-frontend'))

    def test_050_login_with_wrong_credentials(self):
        """
        login with wrong credentials fails
        """
        formid = 'LoginWebuser'
        form = DeformFormObject(self, login_form(), formid)
        form.login_email.set('a@webuser.test')
        form.login_password.set('wrongpassword')
        form.submit()
        self.assertIn("Login failed", self.cli.page_source)

    def test_060_login_with_right_credentials(self):
        """
        login with right credentials logs user in
        """
        formid = 'LoginWebuser'
        form = DeformFormObject(self, login_form(), formid)
        form.login_email.set('a@webuser.test')
        form.login_password.set('awebuser')
        form.submit()
        self.assertTrue(self.cli.find_elements(By.CLASS_NAME, 'cs-backend'))

    # TODO: move to test class for other general portal functionality
    def _test_070_check_locale(self):
        # formid = 'LoginWebuser'
        # form = DeformFormObject(self, login_form(), formid)
        # TODO: fix and move to an own test class for general GUI functionality
        # This throws ElementNotInteractableException: Message: Element
        # <div class="cs-langflags"> could not be scrolled into view
        # self.cli.find_elements(By.CLASS_NAME, "cs-langflags")[0].click()
        # self.assertTrue(self.cli.get_cookie("_LOCALE_") == "en",
        #                "Clicking English flag doesn't set the correct locale"
        #                 "cookie")
        # self.cli.find_elements(By.CLASS_NAME, "cs-langflags")[1].click()
        # self.assertTrue(self.cli.get_cookie("_LOCALE_") == "de",
        #                 "Clicking German flag doesn't set the correct locale"
        #                 "cookie")
        # self.assertTrue(form._form.buttons[0].title[1:] == u'bernehmen',
        #                 "German locale doesn't work")
        # self.cli.find_elements(By.CLASS_NAME, "cs-langflags")[0].click()
        # self.assertTrue(self.cli.get_cookie("_LOCALE_") == "en",
        #                 "Clicking English flag doesn't reset the correct "
        #                 "locale cookie")
        # self.assertTrue(form._form.buttons[0] == u'Submit',
        #                 "English locale doesn't work")
        self.assertTrue(True)
