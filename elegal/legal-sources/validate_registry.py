from pathlib import Path
from urllib.parse import urlparse

import yaml


REGISTRY_PATH = Path("elegal/legal-sources/registry/2026-08-31.yaml")

EXPECTED_IDS = {
    "MV-ACT-10-2026",
    "MV-ACT-11-2026",
    "MV-ACT-12-2026",
    "MV-ACT-13-2026",
    "MV-ACT-14-2026",
    "MV-ACT-15-2026",
    "MV-ACT-16-2026",
    "MV-REG-73-R-2026",
}

REQUIRED_INSTRUMENT_FIELDS = {
    "id",
    "citation",
    "title_en",
    "publication_date",
    "source_authority",
    "gazette_url",
    "language",
    "translation_status",
    "supersession_repeal_status",
    "commencement_status",
    "commencement_rule_source_class",
    "commencement_rule_source_url",
    "enacted_text_commencement_status",
    "effective_date_basis",
    "practice_areas",
    "impact",
    "ingestion_state",
    "source_hash_status",
}

REQUIRED_CLAIM_FIELDS = {
    "claim_id",
    "text",
    "support_classification",
    "exact_source_uri",
    "provision_reference",
    "source_status",
    "retrieval_snapshot",
    "human_review_state",
}

ALLOWED_SUPPORT = {
    "PRIMARY_DIRECT",
    "PRIMARY_INFERENTIAL",
    "MULTIPLE_PRIMARY_AUTHORITIES",
    "CONFLICTING_PRIMARY_AUTHORITY",
    "SECONDARY_CORROBORATION",
    "SECONDARY_ONLY",
    "NO_PRIMARY_SUPPORT",
}

ALLOWED_SOURCE_HOSTS = {
    "gazette.gov.mv",
    "www.gazette.gov.mv",
    "presidency.gov.mv",
    "www.presidency.gov.mv",
}


def require_https_official(url: str, field: str) -> None:
    parsed = urlparse(url)
    assert parsed.scheme == "https", f"{field} must use https: {url}"
    assert parsed.netloc in ALLOWED_SOURCE_HOSTS, f"{field} host is not allow-listed: {url}"


def validate_registry(path: Path = REGISTRY_PATH) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert data["registry_version"] == "1.1"
    assert data["jurisdiction"] == "MV"
    assert data["snapshot_date"] == "2026-08-31"

    instruments = data["instruments"]
    assert isinstance(instruments, list) and instruments, "registry instruments must be a non-empty list"

    ids = {item["id"] for item in instruments}
    assert EXPECTED_IDS.issubset(ids), f"missing expected instruments: {sorted(EXPECTED_IDS - ids)}"

    claim_ids: set[str] = set()

    for item in instruments:
        missing = REQUIRED_INSTRUMENT_FIELDS - set(item)
        assert not missing, f"{item.get('id', '<unknown>')} missing required fields: {sorted(missing)}"

        assert item["source_authority"] == "OFFICIAL_GAZETTE"
        assert item["publication_date"] == "2026-08-31"
        assert item["ingestion_state"] == "SOURCE_VERIFIED_METADATA"
        assert item["source_hash_status"] == "PENDING_SOURCE_ARCHIVE"
        assert item["language"] == "dv"
        assert item["translation_status"], f"{item['id']} translation_status must be explicit"
        assert item["supersession_repeal_status"], f"{item['id']} later-treatment status must be explicit"
        assert item["enacted_text_commencement_status"], f"{item['id']} enacted-text commencement status must be explicit"

        require_https_official(item["gazette_url"], "gazette_url")
        require_https_official(item["commencement_rule_source_url"], "commencement_rule_source_url")

        status = item["commencement_status"]
        effective_date = item.get("effective_date")
        commencement_rule = item.get("commencement_rule")

        if status == "IN_FORCE":
            assert effective_date, f"{item['id']} is IN_FORCE but has no effective_date"
            assert commencement_rule, f"{item['id']} is IN_FORCE but has no commencement evidence"
        elif status == "ENACTED_NOT_YET_EFFECTIVE":
            assert commencement_rule, f"{item['id']} lacks a commencement rule"
        elif status == "PENDING_FULL_TEXT_VERIFICATION":
            assert item["effective_date_basis"] == "PENDING_FULL_TEXT_VERIFICATION"
        else:
            raise AssertionError(f"{item['id']} has unsupported commencement_status: {status}")

        if effective_date:
            assert item["effective_date_basis"], f"{item['id']} effective_date requires an evidence basis"
            assert commencement_rule, f"{item['id']} effective_date requires preserved commencement evidence"

        impacts = item["impact"]
        assert isinstance(impacts, list), f"{item['id']} impact must be a list"

        for claim in impacts:
            assert isinstance(claim, dict), f"{item['id']} impact entries must be provenance objects, not bare strings"
            missing_claim = REQUIRED_CLAIM_FIELDS - set(claim)
            assert not missing_claim, f"{item['id']} claim missing fields: {sorted(missing_claim)}"

            claim_id = claim["claim_id"]
            assert claim_id not in claim_ids, f"duplicate claim_id: {claim_id}"
            claim_ids.add(claim_id)

            assert claim["support_classification"] in ALLOWED_SUPPORT
            require_https_official(claim["exact_source_uri"], "exact_source_uri")
            assert claim["source_status"] == "SOURCE_VERIFIED_METADATA"
            assert claim["retrieval_snapshot"] == "2026-08-31"
            assert claim["human_review_state"] == "PENDING_LEGAL_QA"
            assert claim["provision_reference"], f"{claim_id} provision reference must be explicit"

            # Metadata-only records cannot claim direct provision support before
            # authoritative full text has been acquired and parsed.
            assert claim["support_classification"] != "PRIMARY_DIRECT", (
                f"{claim_id} cannot be PRIMARY_DIRECT at SOURCE_VERIFIED_METADATA"
            )

        notes = item.get("operational_notes", [])
        assert isinstance(notes, list)
        assert all(isinstance(note, str) and note.strip() for note in notes)

    print(
        f"E-LEGAL EF-05 registry validated: {len(instruments)} source records, "
        f"{len(claim_ids)} provenance-bound legal claims"
    )


if __name__ == "__main__":
    validate_registry()
