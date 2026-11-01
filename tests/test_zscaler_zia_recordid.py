"""ZIA recordid must be an exact decimal string in the JSON text."""

from datetime import datetime, timezone
from pathlib import Path
import random
import re
import unittest

from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment


TEMPLATE = (
    Path(__file__).resolve().parents[1]
    / "templates/zscaler/zia/web_security/web_traffic.j2"
)
RECORD_ID = re.compile(r'"recordid"\s*:\s*"(\d+)"')
BARE_RECORD_ID = re.compile(r'"recordid"\s*:\s*\d')
MIN_RECORD_ID = 10**18
MAX_RECORD_ID = 9223372036854775807


def render_web_traffic(seed=17):
    rng = random.Random(seed)
    instant = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    env = SandboxedEnvironment(undefined=StrictUndefined)
    env.filters.update(
        unix_timestamp=lambda value: int(value.timestamp()),
        strftime=lambda value, fmt: value.strftime(fmt),
        random=rng.choice,
    )
    env.globals.update(
        now=lambda: instant,
        registry={
            "get_random_user": lambda: {
                "email": "analyst@example.com",
                "department": "Security",
                "location": {"city": "Headquarters"},
            },
            "get_random_device": lambda: {
                "ip_address": "192.0.2.10",
                "hostname": "workstation-1",
                "model": "Latitude",
                "os_type": "Windows",
                "os_version": "11",
            },
            "get_organization_field": lambda field: "example.com",
        },
        fake=type("Fake", (), {"random_element": staticmethod(lambda elements: elements[0])})(),
        random_int=rng.randint,
        random_string=lambda length, chars: "".join(rng.choices(chars, k=length)),
        random_public_ip=lambda: "203.0.113.10",
    )
    return env.from_string(TEMPLATE.read_text()).render()


class ZiaRecordIdTests(unittest.TestCase):
    def test_recordid_is_exact_decimal_string(self):
        for seed in range(20):
            raw = render_web_traffic(seed)
            self.assertIsNone(
                BARE_RECORD_ID.search(raw),
                "recordid was emitted as a JSON number",
            )
            match = RECORD_ID.search(raw)
            self.assertIsNotNone(match, raw[:200])
            digits = match.group(1)
            value = int(digits)
            self.assertEqual(str(value), digits)
            self.assertGreaterEqual(value, MIN_RECORD_ID)
            self.assertLessEqual(value, MAX_RECORD_ID)
