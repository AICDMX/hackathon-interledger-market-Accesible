from django.test import TestCase, Client


class DemoGuideTest(TestCase):
    def test_get_shows_password_form(self):
        response = self.client.get("/demo/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "password")

    def test_wrong_password_shows_error(self):
        response = self.client.post("/demo/", {"password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wrong password")

    def test_correct_password_shows_guide(self):
        response = self.client.post("/demo/", {"password": "accessovox"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "demo_funder")
        self.assertContains(response, "carlos_otomi")

    def test_session_persists_after_auth(self):
        # First auth
        self.client.post("/demo/", {"password": "accessovox"})
        # Second request should not need password
        response = self.client.get("/demo/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "demo_funder")

    def test_guide_shows_stats(self):
        self.client.post("/demo/", {"password": "accessovox"})
        response = self.client.get("/demo/")
        # Should have stat numbers in the page
        self.assertContains(response, "Users")
        self.assertContains(response, "Jobs")
        self.assertContains(response, "Applications")
