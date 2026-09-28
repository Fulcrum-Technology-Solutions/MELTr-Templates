"""Verify the GlobalProtect CSV contract with fixed clocks; no services or delivery."""
import csv
from datetime import datetime, timezone
from pathlib import Path
import random
from types import SimpleNamespace
import unittest
from zoneinfo import ZoneInfo

from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment

TEMPLATE = Path(__file__).resolve().parents[1] / "templates/paloalto/pan-os/globalprotect/globalprotect.j2"


def render_event(instant, seed=17):
    rng = random.Random(seed)
    calls = []
    def clock():
        calls.append(instant)
        return instant
    env = SandboxedEnvironment(undefined=StrictUndefined)
    env.filters.update(format_timestamp=lambda value, fmt: value.strftime(fmt), random=rng.choice)
    env.globals.update(
        current_timestamp=clock,
        registry=SimpleNamespace(
            get_random_user=lambda: SimpleNamespace(user_id="test.user"),
            get_random_device=lambda: SimpleNamespace(hostname="test-device", ip_address="192.0.2.10"),
        ),
        random_int=rng.randint,
        random_string=lambda length, chars: "".join(rng.choices(chars, k=length)),
        random_public_ip=lambda: "203.0.113.10",
        random_guid=lambda: "00000000-0000-4000-8000-000000000001",
    )
    output = env.from_string(TEMPLATE.read_text()).render()
    return output, calls


class GlobalProtectFormatTests(unittest.TestCase):
    def test_csv_quoting_and_field_positions(self):
        statuses = set()
        for seed in range(50):
            with self.subTest(seed=seed):
                output, calls = render_event(datetime(2026, 9, 28, 12, 34, 56, 123456, tzinfo=timezone.utc), seed)
                self.assertTrue(output.startswith(","), "No leading blank record")
                rows = list(csv.reader(output.splitlines(), strict=True))
                self.assertEqual(len(rows), 1)
                fields = rows[0]
                self.assertEqual(len(fields), 50)
                self.assertEqual(fields[3], "GLOBALPROTECT")
                self.assertEqual(fields[40], f"{fields[41]},{fields[38]},{fields[39]}")
                self.assertIn(f'"{fields[40]}"', output)
                self.assertTrue(fields[41].startswith("gp-gateway-"))
                self.assertTrue(all(value.isdigit() for value in fields[42:46]))
                self.assertEqual(fields[46], fields[7])
                self.assertEqual(fields[47], "test-device")
                self.assertTrue(fields[48].isdigit())
                self.assertEqual(fields[49], "")  # Existing 11.1+ Cluster Name slot.
                self.assertEqual(len(calls), 1)
                statuses.add(fields[28])
        self.assertEqual(statuses, {"success", "failure"})

    def test_timestamps_share_instant_and_actual_offset(self):
        instants = [
            datetime(2026, 9, 28, 12, 34, 56, micro, tzinfo=timezone.utc)
            for micro in [0, 123456, 999999]
        ] + [
            datetime(2026, month, 4, 12, 34, 56, 123456, tzinfo=ZoneInfo(zone))
            for zone in ["America/Chicago", "Asia/Kolkata"] for month in [1, 9]
        ] + [
            datetime.fromisoformat(value).astimezone(ZoneInfo("America/Chicago"))
            for value in ["2026-03-08T07:59:59.123456+00:00", "2026-03-08T08:00:00.123456+00:00",
                          "2026-11-01T06:30:00.123456+00:00", "2026-11-01T07:30:00.123456+00:00"]
        ]
        for instant in instants:
            with self.subTest(instant=instant):
                output, calls = render_event(instant)
                fields = next(csv.reader([output.strip()], strict=True))
                self.assertEqual(fields[1], instant.strftime("%Y/%m/%d %H:%M:%S"))
                self.assertEqual(fields[6], fields[1])
                self.assertRegex(fields[36], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}$")
                parsed = datetime.fromisoformat(fields[36])
                self.assertEqual(parsed.utcoffset(), instant.utcoffset())
                self.assertEqual(parsed.astimezone(timezone.utc), instant.replace(microsecond=instant.microsecond // 1000 * 1000).astimezone(timezone.utc))
                self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
