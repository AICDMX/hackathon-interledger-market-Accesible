from django.test import TestCase, Client
from django.urls import reverse

from users.models import User
from users.forms import ProfileForm, PasswordChangeForm


class UserModelTest(TestCase):
    def test_str_returns_pretty_name(self):
        user = User.objects.create_user(
            username="testuser", password="pass", pretty_name="Display Name"
        )
        self.assertEqual(str(user), "Display Name")

    def test_str_falls_back_to_username(self):
        user = User.objects.create_user(username="testuser", password="pass")
        self.assertEqual(str(user), "testuser")

    def test_get_display_name(self):
        user = User.objects.create_user(
            username="u", password="p", pretty_name="Pretty"
        )
        self.assertEqual(user.get_display_name(), "Pretty")
        user.pretty_name = ""
        self.assertEqual(user.get_display_name(), "u")

    def test_get_native_languages_list(self):
        user = User.objects.create_user(
            username="u", password="p", native_languages="nahuatl, otomi, quechua"
        )
        self.assertEqual(
            user.get_native_languages_list(), ["nahuatl", "otomi", "quechua"]
        )

    def test_get_native_languages_list_empty(self):
        user = User.objects.create_user(username="u", password="p")
        self.assertEqual(user.get_native_languages_list(), [])

    def test_is_funder(self):
        funder = User.objects.create_user(username="f", password="p", role="funder")
        creator = User.objects.create_user(username="c", password="p", role="creator")
        both = User.objects.create_user(username="b", password="p", role="both")
        self.assertTrue(funder.is_funder())
        self.assertFalse(creator.is_funder())
        self.assertTrue(both.is_funder())

    def test_is_creator(self):
        funder = User.objects.create_user(username="f", password="p", role="funder")
        creator = User.objects.create_user(username="c", password="p", role="creator")
        both = User.objects.create_user(username="b", password="p", role="both")
        self.assertFalse(funder.is_creator())
        self.assertTrue(creator.is_creator())
        self.assertTrue(both.is_creator())

    def test_new_user_gets_staff_and_superuser(self):
        user = User.objects.create_user(username="u", password="p")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_get_seller_private_key_none(self):
        user = User.objects.create_user(username="u", password="p")
        self.assertIsNone(user.get_seller_private_key())

    def test_get_seller_private_key_string(self):
        user = User.objects.create_user(
            username="u", password="p", seller_private_key="  my-key  "
        )
        self.assertEqual(user.get_seller_private_key(), "my-key")

    def test_get_seller_private_key_bytes(self):
        user = User(username="u", seller_private_key="key-data")
        # Simulate bytes
        user.seller_private_key = b"key-bytes"
        self.assertEqual(user.get_seller_private_key(), "key-bytes")

    def test_default_role_is_both(self):
        user = User.objects.create_user(username="u", password="p")
        self.assertEqual(user.role, "both")


class RegisterViewTest(TestCase):
    def test_get_register_page(self):
        response = self.client.get("/users/register/")
        self.assertEqual(response.status_code, 200)

    def test_register_success(self):
        response = self.client.post(
            "/users/register/",
            {
                "username": "newuser",
                "email": "new@test.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "role": "creator",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        user = User.objects.get(username="newuser")
        self.assertEqual(user.role, "creator")

    def test_register_password_mismatch(self):
        response = self.client.post(
            "/users/register/",
            {
                "username": "newuser",
                "email": "new@test.com",
                "password1": "pass1",
                "password2": "pass2",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_register_duplicate_username(self):
        User.objects.create_user(username="existing", password="pass")
        response = self.client.post(
            "/users/register/",
            {
                "username": "existing",
                "email": "new@test.com",
                "password1": "pass",
                "password2": "pass",
            },
        )
        self.assertEqual(response.status_code, 200)


class RegisterCreatorViewTest(TestCase):
    def test_get_page(self):
        response = self.client.get("/users/register/creator/")
        self.assertEqual(response.status_code, 200)

    def test_creates_funder_role(self):
        response = self.client.post(
            "/users/register/creator/",
            {
                "username": "newfunder",
                "email": "f@test.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="newfunder")
        self.assertEqual(user.role, "funder")


class RegisterDoerViewTest(TestCase):
    def test_get_page(self):
        response = self.client.get("/users/register/doer/")
        self.assertEqual(response.status_code, 200)

    def test_creates_creator_role(self):
        response = self.client.post(
            "/users/register/doer/",
            {
                "username": "newdoer",
                "email": "d@test.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="newdoer")
        self.assertEqual(user.role, "creator")


class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="profuser", password="pass", email="old@test.com"
        )

    def test_requires_login(self):
        response = self.client.get("/users/profile/")
        self.assertEqual(response.status_code, 302)

    def test_get_profile_page(self):
        self.client.login(username="profuser", password="pass")
        response = self.client.get("/users/profile/")
        self.assertEqual(response.status_code, 200)

    def test_update_profile(self):
        self.client.login(username="profuser", password="pass")
        response = self.client.post(
            "/users/profile/",
            {
                "update_profile": "1",
                "email": "new@test.com",
                "preferred_language": "es",
                "role": "creator",
                "pretty_name": "New Name",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@test.com")
        self.assertEqual(self.user.pretty_name, "New Name")

    def test_change_password(self):
        self.client.login(username="profuser", password="pass")
        response = self.client.post(
            "/users/profile/",
            {
                "change_password": "1",
                "old_password": "pass",
                "new_password1": "NewStrongPass456!",
                "new_password2": "NewStrongPass456!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass456!"))

    def test_change_password_wrong_old(self):
        self.client.login(username="profuser", password="pass")
        response = self.client.post(
            "/users/profile/",
            {
                "change_password": "1",
                "old_password": "wrongpass",
                "new_password1": "NewPass456!",
                "new_password2": "NewPass456!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("pass"))


class ProfileFormTest(TestCase):
    def test_clean_email_unique(self):
        user1 = User.objects.create_user(
            username="u1", password="p", email="taken@test.com"
        )
        user2 = User.objects.create_user(
            username="u2", password="p", email="other@test.com"
        )
        form = ProfileForm(
            data={
                "email": "taken@test.com",
                "preferred_language": "en",
                "role": "both",
            },
            instance=user2,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_same_email_is_ok(self):
        user = User.objects.create_user(
            username="u", password="p", email="same@test.com"
        )
        form = ProfileForm(
            data={
                "email": "same@test.com",
                "preferred_language": "en",
                "role": "both",
            },
            instance=user,
        )
        self.assertTrue(form.is_valid())


class PasswordChangeFormTest(TestCase):
    def test_wrong_old_password(self):
        user = User.objects.create_user(username="u", password="correct")
        form = PasswordChangeForm(
            user=user,
            data={
                "old_password": "wrong",
                "new_password1": "NewPass456!",
                "new_password2": "NewPass456!",
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn("old_password", form.errors)

    def test_mismatched_new_passwords(self):
        user = User.objects.create_user(username="u", password="correct")
        form = PasswordChangeForm(
            user=user,
            data={
                "old_password": "correct",
                "new_password1": "NewPass456!",
                "new_password2": "Different789!",
            },
        )
        self.assertFalse(form.is_valid())

    def test_valid_password_change(self):
        user = User.objects.create_user(username="u", password="correct")
        form = PasswordChangeForm(
            user=user,
            data={
                "old_password": "correct",
                "new_password1": "NewStrongPass456!",
                "new_password2": "NewStrongPass456!",
            },
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(user.check_password("NewStrongPass456!"))
