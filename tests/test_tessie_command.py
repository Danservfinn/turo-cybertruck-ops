import json
import unittest
from unittest.mock import Mock, patch

from scripts.tessie_command import (
    CONFIRM_PHRASE,
    build_command_request,
    execute_command,
    redact_receipt,
    validate_confirmation,
)


class TessieCommandTests(unittest.TestCase):
    def test_navigation_destination_uses_share_command_query_value(self):
        request = build_command_request(command="navigate", destination="RDU Terminal 2")

        self.assertEqual(request["endpoint"], "share")
        self.assertEqual(request["query"]["value"], "RDU Terminal 2")
        self.assertEqual(request["query"]["locale"], "en-US")
        self.assertEqual(request["body"], {})
        self.assertEqual(request["risk"], "navigation")

    def test_unlock_and_remote_start_are_allowed_but_high_risk(self):
        unlock = build_command_request(command="unlock")
        remote_start = build_command_request(command="remote-start-drive", password="1234")

        self.assertEqual(unlock["endpoint"], "unlock")
        self.assertEqual(unlock["risk"], "high")
        self.assertEqual(remote_start["endpoint"], "remote_start_drive")
        self.assertEqual(remote_start["body"], {"password": "1234"})
        self.assertEqual(remote_start["risk"], "critical")

    def test_confirmation_is_required_for_execution(self):
        with self.assertRaises(SystemExit):
            validate_confirmation(command="unlock", confirm="wrong")

        self.assertTrue(validate_confirmation(command="unlock", confirm=CONFIRM_PHRASE))

    def test_dry_run_does_not_call_api(self):
        request = build_command_request(command="honk")
        receipt = execute_command(token="secret-token", vin="7G2CEHEE6RA032607", request=request, dry_run=True)

        self.assertTrue(receipt["dry_run"])
        self.assertEqual(receipt["command"], "honk")
        self.assertNotIn("secret-token", json.dumps(receipt))

    def test_execute_posts_without_printing_token_or_raw_vin(self):
        response = Mock()
        response.read.return_value = b'{"result": true, "reason": ""}'
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=None)
        request = build_command_request(command="flash")

        with patch("scripts.tessie_command.urllib.request.urlopen", return_value=response) as urlopen:
            receipt = execute_command(token="secret-token", vin="7G2CEHEE6RA032607", request=request, dry_run=False)

        called_request = urlopen.call_args.args[0]
        self.assertIn("/7G2CEHEE6RA032607/command/flash", called_request.full_url)
        self.assertEqual(called_request.get_method(), "POST")
        rendered_receipt = json.dumps(redact_receipt(receipt))
        self.assertNotIn("secret-token", rendered_receipt)
        self.assertNotIn("7G2CEHEE6RA032607", rendered_receipt)
        self.assertIn("2607", rendered_receipt)


if __name__ == "__main__":
    unittest.main()
