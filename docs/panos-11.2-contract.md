# PAN-OS 11.2 template baseline

The PAN-OS collection targets a documented 11.2 baseline: **117 traffic fields** and **50 GlobalProtect fields**, both ending at Cluster Name. This is the agreed lab profile, corroborated by vendor documentation and Splunk extraction definitions. It is not a claim that every 11.2 patch exports an identical tail.

## Evidence and field positions

The official [11.1-and-later administrator PDF](https://docs.paloaltonetworks.com/content/dam/techdocs/en_US/pdf/pan-os/11-1/pan-os-admin/pan-os-admin.pdf), revised August 8, 2025, lists traffic through Cluster Name on printed pages 661–662 and GlobalProtect through Cluster Name on pages 711–712.

The supplied Splunk Add-on for Palo Alto Networks **4.0.0** archive (`splunk-add-on-for-palo-alto-networks_400.spl`) corroborates those layouts. In `default/props.conf`, `pan:traffic` selects `extract_traffic`; `pan:globalprotect` selects `extract_globalprotect`. In `default/transforms.conf`, their CSV FIELDS lists contain 117 and 50 positions respectively, ending at `cluster_name`. The package contains no release-specific 11.2 field contract. Its extraction definitions establish the mapped baseline, not runtime parsing success. See [Splunk add-on documentation](https://splunk.github.io/splunk-add-on-for-palo-alto-networks/).

Traffic positions 103, 116 and 117 remain High Resolution Timestamp, Flow Type and Cluster Name. GlobalProtect positions 37, 41, 42 and 50 remain High Res Timestamp, Attempted Gateways, Gateway and Cluster Name. Attempted Gateways is one quoted CSV field even though it contains commas; timestamps preserve their actual UTC offset and milliseconds.

The [current consolidated traffic reference](https://docs.paloaltonetworks.com/ngfw/administration/monitoring/use-syslog-for-monitoring/syslog-field-descriptions/traffic-log-fields), inspected September 28, 2026, includes additional fields beyond this baseline. It labels AI/Kubernetes fields as 11.1+, provides no introduction version for eight internal TCP telemetry columns, and restricts the final Advanced Device-ID pair to 12.1.2+. This template deliberately omits all 13 columns after Cluster Name. Their omission defines the lab baseline; it does not assert that they are absent from every 11.2 appliance. Later extensions should have explicit source evidence and parser tests.

[GlobalProtect documentation](https://docs.paloaltonetworks.com/ngfw/administration/monitoring/use-syslog-for-monitoring/syslog-field-descriptions/globalprotect-log-fields) corroborates the 50-field sequence. The GlobalProtect client version is independent of the firewall PAN-OS release and is not changed to 11.2.

## Changes and validation

Traffic changes from 130 to 117 columns without moving any retained column. Flow Type uses documented `Explicit Proxy`, `Transparent Proxy`, or `NonProxyTraffic`, replacing the unsupported synthetic `ProxyTraffic`. Product version metadata changes from 10.2 to 11.2. Existing template IDs and the GlobalProtect quoting/timestamp fixes are preserved.

Offline tests check CSV counts, tail positions, clock consistency, offsets, and attempted-gateway quoting. Repository metadata validation remains required. Rendering and mapping checks do not establish Cribl execution or Splunk/Elastic native parsing.

## Rollout

After this PR and the automated collection-version/index PR merge, sync the registry and refresh installed templates. Preview traffic and GlobalProtect separately in Cribl and verify destination parsing. Any custom parser expecting exactly 130 traffic columns must be reviewed. Existing source filters, Splunk index choices, and Elastic routing are unchanged. No live generator, Pack, or destination is changed by this repository update.

## Metadata field docs vs CSV width

Registry sample preview renders the `.j2`, not `documentation.fields[].example_value`. For wide CSV formats:

| Template | Emitted CSV columns | Documented in `.meta.yaml` |
|----------|---------------------|----------------------------|
| Traffic | 117 (lab baseline) | Curated operator-facing subset; summary states the gap |
| GlobalProtect | 50 | 50/50 with `field_number` (preferred pattern) |
| WildFire threat | Full threat-log CSV row | Curated subset; summary states the gap |

Prefer documenting every emitted column when practical. When documenting a subset, say so in `documentation.overview.summary` and keep this contract as the column-count source of truth.
