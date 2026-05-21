import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.tessie_readonly_probe import build_report, load_fixture_responses, redact_report


class TessieReadonlyProbeTests(unittest.TestCase):
    def test_build_report_summarizes_state_without_location_or_token(self):
        responses = {
            "state": {
                "vehicle_state": {"odometer": 24460.42},
                "charge_state": {
                    "battery_level": 67,
                    "charging_state": "Disconnected",
                    "plugged_in": False,
                },
                "drive_state": {
                    "latitude": 35.7796,
                    "longitude": -78.6382,
                    "shift_state": None,
                },
                "state": "online",
            },
            "drives": {"results": [{"id": "d1"}, {"id": "d2"}]},
            "charges": {"results": [{"id": "c1"}]},
        }

        report = build_report(vin="7G2CEHEE6RA032607", responses=responses)
        rendered = json.dumps(report)

        self.assertEqual(report["vehicle"]["vin_suffix"], "2607")
        self.assertEqual(report["state"]["online_state"], "online")
        self.assertEqual(report["state"]["odometer_miles"], 24460.42)
        self.assertEqual(report["state"]["battery_level_pct"], 67)
        self.assertEqual(report["source_counts"]["drives"], 2)
        self.assertEqual(report["source_counts"]["charges"], 1)
        self.assertNotIn("latitude", rendered.lower())
        self.assertNotIn("longitude", rendered.lower())
        self.assertNotIn("token", rendered.lower())

    def test_redact_report_removes_location_even_if_api_shape_changes(self):
        report = {
            "nested": {
                "latitude": 35.0,
                "longitude": -78.0,
                "lat": 35.0,
                "lon": -78.0,
                "gps_as_of": 123,
                "ok": True,
            }
        }
        redacted = redact_report(report)
        self.assertEqual(redacted, {"nested": {"ok": True}})

    def test_load_fixture_responses_loads_endpoint_json_files(self):
        with TemporaryDirectory() as tmp:
            fixture_dir = Path(tmp)
            (fixture_dir / "state.json").write_text('{"state": "online"}')
            (fixture_dir / "drives.json").write_text('{"results": []}')
            (fixture_dir / "charges.json").write_text('{"results": []}')

            responses = load_fixture_responses(fixture_dir)

        self.assertEqual(set(responses), {"state", "drives", "charges"})
        self.assertEqual(responses["state"]["state"], "online")


if __name__ == "__main__":
    unittest.main()
