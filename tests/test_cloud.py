import json
import unittest

from marginalia.cloud import CloudClient, validate_config


class CloudTests(unittest.TestCase):
    def test_rejects_insecure_configuration(self):
        self.assertFalse(validate_config("http://example.com", "key"))
        self.assertFalse(validate_config("https://example.supabase.co", ""))
        self.assertFalse(validate_config("https://example.supabase.co", "sb_secret_do-not-use"))
        self.assertFalse(validate_config("https://example.supabase.co", "service_role"))
        self.assertTrue(validate_config("https://example.supabase.co", "sb_publishable_test"))

    def test_password_login_and_conditional_update(self):
        calls = []

        def request(method, url, headers, body):
            calls.append((method, url, headers, body))
            if "grant_type=password" in url:
                return {"access_token": "access", "refresh_token": "refresh", "expires_in": 3600, "user": {"id": "user-1", "email": "me@example.com"}}
            return [{"id": "card-1", "revision": 3, "kind": "word", "word": "criterion", "meaning": "准则", "sentence": "", "translation": "", "structure": "", "source": "", "tags": "", "status": "待复习", "deleted": False}]

        client = CloudClient("https://example.supabase.co", "sb_publishable_test", request=request)
        self.assertEqual(client.sign_in("me@example.com", "password")["user"]["id"], "user-1")
        self.assertIn("/auth/v1/token?grant_type=password", calls[0][1])
        self.assertEqual(json.loads(calls[0][3])["password"], "password")
        updated = client.update_card({"id": "card-1", "kind": "word", "word": "criterion", "meaning": "准则"}, 2)
        self.assertEqual(updated["revision"], 3)
        self.assertIn("revision=eq.2", calls[1][1])
        self.assertEqual(json.loads(calls[1][3])["revision"], 3)


if __name__ == "__main__":
    unittest.main()
