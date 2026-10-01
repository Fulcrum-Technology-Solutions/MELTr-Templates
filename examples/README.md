# Examples Directory

This directory contains a **minimal starter layout** for MELTr templates. It is skipped by CI validation (`python .github/scripts/validate_templates.py`).

## Prefer real templates as the standard

For hierarchy, metadata shape, and Jinja authoring patterns, copy from production templates under `templates/` — especially:

- `templates/paloalto/pan-os/firewall/traffic.*` (wide CSV + curated field docs)
- `templates/paloalto/pan-os/globalprotect/globalprotect.*` (full field_number coverage)

Do **not** treat undeclared root keys (`parameters`, `context`) as part of the template contract; they are forbidden by `schemas/template.schema.json`.

## Structure

```
examples/
  acme/
    vendor.meta.yaml
    widget/
      product.meta.yaml
      collection.json
      telemetry/
        device_online.j2
        device_online.meta.yaml
```

Required template meta fields: `vendor`, `product`, `data_source`, `description`, `format` (IDs lowercase, matching directory names).
