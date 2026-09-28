# PAN-OS 11.2 template assessment

Status: draft; traffic release-specific tail verification remains open. Do not publish this change as a verified default PAN-OS 11.2 format yet.

Both existing template IDs remain unchanged. No live generator, Pack, or destination configuration is changed.

## Verified changes

The current [official traffic field reference](https://docs.paloaltonetworks.com/ngfw/administration/monitoring/use-syslog-for-monitoring/syslog-field-descriptions/traffic-log-fields), inspected 2026-09-28, lists 130 columns. Its last two Advanced Device-ID fields are explicitly restricted to PAN-OS 12.1.2 and later. This draft removes those two empty trailing columns, leaving all earlier positions unchanged. Traffic becomes 128 columns instead of 130.

The reference explicitly labels Cluster Name, AI Traffic, AI Forward Error and K8S Cluster ID as 11.1 and later. The eight intervening internal TCP telemetry columns have no release-introduction annotation. They are retained in this draft; their presence in the native 11.2 default export has NOT been established. A 128-column profile must not be mistaken for verified appliance output.

[GlobalProtect field documentation](https://docs.paloaltonetworks.com/ngfw/administration/monitoring/use-syslog-for-monitoring/syslog-field-descriptions/globalprotect-log-fields) defines 50 positions and labels Cluster Name as 11.1 and later. The recently merged quoting and timestamp fixes remain intact. The GlobalProtect app version field is not the PAN-OS version; do not replace it with 11.2.

The official [11.1-and-later administrator PDF](https://docs.paloaltonetworks.com/content/dam/techdocs/en_US/pdf/pan-os/11-1/pan-os-admin/pan-os-admin.pdf), revised August 8, 2025, lists traffic through Cluster Name on printed pages 661–662 (117 fields), and GlobalProtect through Cluster Name on pages 711–712 (50 fields). This older snapshot differs from the current web guide and reinforces the need to identify the exact 11.2 patch/export contract; it does not prove that newer fields are absent from all 11.2 releases.

The traffic Flow Type enumeration also replaces the unsupported synthetic `ProxyTraffic` with documented `Explicit Proxy` and `Transparent Proxy`, retaining `NonProxyTraffic`.

## Remaining release gate

Obtain one unmodified default-format TRAFFIC syslog event from a known PAN-OS 11.2 patch release, or an authoritative release-specific field sequence. Record the exact patch and forwarding format. Confirm whether the eight internal TCP telemetry slots occur after K8S Cluster ID. Historical 11.2 administration links redirect to the consolidated guide; the former 11.2 PDF URL returns 404. The current guide alone does not resolve this tail.

Then finalize the traffic column count, set product metadata from 10.2 to 11.2, and update these notes/tests. This draft intentionally leaves product version unchanged until that gate is resolved. Keep CSV-aware position tests, timestamp offset tests, and GlobalProtect attempted-gateway quoting tests. Do not infer native parsing success from rendering tests.

## Rollout

After the final reviewed PR and automated collection-version/index PR merge, sync the registry and refresh installed templates. Preview traffic and GlobalProtect separately in Cribl and verify destination parsing. The traffic column-count change needs explicit review for any custom parser expecting 130 columns. Existing template IDs, source matching, Splunk index choices, and Elastic routing are unchanged.
