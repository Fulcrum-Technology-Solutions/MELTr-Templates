"""Render the complete traffic CSV with fixed clocks; no services or delivery."""

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
import random
from types import SimpleNamespace
import unittest
from zoneinfo import ZoneInfo

from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment


TEMPLATE = (
    Path(__file__).resolve().parents[1]
    / "templates/paloalto/pan-os/firewall/traffic.j2"
)


def render_traffic(instant):
    """Use the public datetime/filter contract with deterministic non-time data."""
    rng = random.Random(17)
    clock_calls = 0

    def clock():
        nonlocal clock_calls
        clock_calls += 1
        return instant

    env = SandboxedEnvironment(undefined=StrictUndefined)
    env.filters.update(
        format_timestamp=lambda value, fmt: value.strftime(fmt),
        subtract_seconds=lambda value, seconds: value - timedelta(seconds=seconds),
        random=rng.choice,
    )
    env.globals.update(
        now=clock,
        current_timestamp=clock,
        registry=SimpleNamespace(
            get_random_device=lambda: None,
            get_random_user=lambda: None,
        ),
        random_int=rng.randint,
        random_string=lambda length, chars: "".join(rng.choices(chars, k=length)),
        random_private_ip=lambda: "192.168.1.10",
        random_public_ip=lambda: "203.0.113.10",
        random_guid=lambda: "00000000-0000-4000-8000-000000000001",
    )
    output = env.from_string(TEMPLATE.read_text()).render()
    rows = list(csv.reader(output.splitlines()))
    return rows, clock_calls


class TrafficTimestampTests(unittest.TestCase):
    def assert_timestamps(self, instant, expected):
        rows, clock_calls = render_traffic(instant)
        self.assertEqual(len(rows), 1)
        fields = rows[0]
        self.assertEqual(len(fields), 128)
        self.assertEqual(fields[3], "TRAFFIC")
        self.assertIn(fields[115], {"NonProxyTraffic", "Explicit Proxy", "Transparent Proxy"})
        self.assertEqual(fields[116:120], ["", "0", "0", ""])
        self.assertEqual(fields[120:], ["0"] * 8)  # Preserved internal TCP slots; no 12.1.2 Device-ID tail.
        # Receive Time, Generated Time and High Resolution Timestamp keep their
        # existing CSV positions (zero-based 1, 6 and 102).
        self.assertEqual(fields[1], instant.strftime("%Y/%m/%d %H:%M:%S"))
        self.assertEqual(fields[6], fields[1])
        self.assertEqual(fields[102], expected)
        self.assertEqual(clock_calls, 1)
        parsed = datetime.fromisoformat(fields[102])
        self.assertEqual(parsed.utcoffset(), instant.utcoffset())
        self.assertEqual(
            parsed.astimezone(timezone.utc),
            instant.replace(microsecond=instant.microsecond // 1000 * 1000)
            .astimezone(timezone.utc),
        )

    def test_utc_and_millisecond_precision(self):
        for micros, fraction in [(0, "000"), (128543, "128"), (999999, "999")]:
            with self.subTest(microsecond=micros):
                self.assert_timestamps(
                    datetime(2026, 9, 4, 21, 6, 31, micros, tzinfo=timezone.utc),
                    f"2026-09-04T21:06:31.{fraction}+00:00",
                )

    def test_chicago_summer_and_winter_offsets(self):
        for month, offset in [(9, "-05:00"), (1, "-06:00")]:
            with self.subTest(month=month):
                self.assert_timestamps(
                    datetime(2026, month, 4, 21, 6, 31, 128543,
                             tzinfo=ZoneInfo("America/Chicago")),
                    f"2026-{month:02d}-04T21:06:31.128{offset}",
                )

    def test_chicago_dst_transitions(self):
        cases = [
            ("2026-03-08T07:59:59.123456+00:00", "2026-03-08T01:59:59.123-06:00"),
            ("2026-03-08T08:00:00.123456+00:00", "2026-03-08T03:00:00.123-05:00"),
            ("2026-11-01T06:30:00.123456+00:00", "2026-11-01T01:30:00.123-05:00"),
            ("2026-11-01T07:30:00.123456+00:00", "2026-11-01T01:30:00.123-06:00"),
        ]
        for utc, expected in cases:
            with self.subTest(utc=utc):
                instant = datetime.fromisoformat(utc).astimezone(ZoneInfo("America/Chicago"))
                self.assert_timestamps(instant, expected)

    def test_positive_half_hour_offset(self):
        self.assert_timestamps(
            datetime(2026, 9, 4, 21, 6, 31, 128543, tzinfo=ZoneInfo("Asia/Kolkata")),
            "2026-09-04T21:06:31.128+05:30",
        )


if __name__ == "__main__":
    unittest.main()
