import pytest
import json
import re

def test_proto_parity_with_json_schema():
    with open("mnos/core/schema/mnos_event_schema_v1_1.json", "r") as f:
        json_schema = json.load(f)

    with open("proto/mnos_event_v1_1.proto", "r") as f:
        proto_content = f.read()

    # Check for core fields
    required_fields = json_schema["required"]
    for field in required_fields:
        assert re.search(rf"\b{field}\b", proto_content)

    # Check for nested structures
    assert "message Tenant" in proto_content
    assert "brand" in proto_content
    assert "tin" in proto_content
    assert "jurisdiction" in proto_content

    assert "message Metadata" in proto_content
    assert "schema_version" in proto_content
