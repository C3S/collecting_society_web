# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal.repertoire

from collecting_society_portal.tests.base import (
    IntegrationTestBase,
    DeformFormObject
)

from collecting_society_portal.views.forms.login_web_user import login_form
from collecting_society_portal.models import Tdb, WebUser

from ...views.forms.register_webuser import (
    claims_membership_form,
    wants_membership_form,
    register_member_form,
    register_nonmember_form
)


class TestWebUser(IntegrationTestBase):

    def test_010_registration(self):
        """
        registration registers user
        """
        self.url()
        self.screenshot()
        formid = 'RegisterWebuser'
        form = DeformFormObject(self.cli, claims_membership_form(), formid)
        form.claims_membership()
        form = DeformFormObject(self.cli, register_nonmember_form(), formid)
        form.firstname.set('Firstname')
        form.lastname.set('Lastname')
        form.birthdate.set('1970-01-01')
        form.register_email.set('a@webuser.test')
        form.register_password.set('awebuser')
        form.terms_accepted.set(True)
        self.screenshot()
        form.register_webuser()
        self.screenshot()
        self.assertIn("Thank you for your registration", self.cli.page_source)

    def test_020_login_before_validation(self):
        """
        login before validation fails
        """
        formid = 'LoginWebuser'
        form = DeformFormObject(self.cli, login_form(), formid)
        form.login_email.set('a@webuser.test')
        form.login_password.set('awebuser')
        self.screenshot()
        form.submit()
        self.screenshot()
        self.assertIn("User mail address not verified", self.cli.page_source)

    @Tdb.transaction(readonly=False)
    def test_030_validate_user_registration(self):
        """
        validate user registration succeeds and logs user in
        """
        webuser = WebUser.search_by_email('a@webuser.test')
        self.assertEqual(webuser.opt_in_state, "mail-sent")
        self.url("verify_email/" + webuser.opt_in_uuid)
        self.screenshot()
        self.assertTrue(
            self.cli.find_elements_by_class_name('cs-backend')
        )

    def test_040_logout(self):
        """
        logout logs user out
        """
        self.url('logout')
        self.assertTrue(
            self.cli.find_elements_by_class_name('cs-frontend')
        )

    def test_050_login_with_wrong_credentials(self):
        """
        login with wrong credentials fails
        """
        formid = 'LoginWebuser'
        form = DeformFormObject(self.cli, login_form(), formid)
        form.login_email.set('a@webuser.test')
        form.login_password.set('wrongpassword')
        form.submit()
        self.screenshot()
        self.assertIn("Login failed", self.cli.page_source)

    def test_060_login_with_right_credentials(self):
        """
        login with right credentials logs user in
        """
        formid = 'LoginWebuser'
        form = DeformFormObject(self.cli, login_form(), formid)
        form.login_email.set('a@webuser.test')
        form.login_password.set('awebuser')
        form.submit()
        self.screenshot()
        self.assertTrue(
            self.cli.find_elements_by_class_name('cs-backend')
        )
