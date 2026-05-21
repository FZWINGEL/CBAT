"""Dataset manifest assembly and metadata extraction."""

from __future__ import annotations

import subprocess
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from mbp import __version__
from mbp.audit.inventory import build_archive_inventory, build_inventory, utc_now_iso
from mbp.audit.models import DatasetManifest, FileInventoryRecord, Provenance, SCHEMA_VERSION

EXPECTED_AUDIT_REQUIREMENTS = [
    "archive name, DOI, source, and download date",
    "SHA-256 hash for every observed file and archive",
    "extracted file count for each archive",
    "row count by file family where tabular rows can be counted safely",
    "cell count by modality",
    "condition count and 76 parameter sets x 3 replicate verification",
    "EIS coverage by cell/SOC/temperature/check-up",
    "PULSE coverage by cell/SOC/temperature/check-up",
    "LOG and LOG_AGE availability",
    "known anomalies and data gaps",
    "preprocessing script commit hash",
    "generated table schema version",
]

MODALITY_FAMILIES = ("cfg", "eoc", "eis", "pulse", "log", "log_age")


def parse_bag_info(bag_info_path: Path) -> dict[str, str]:
    """Parse key-value metadata from bag-info.txt."""
    if not bag_info_path.exists():
        return {}
    metadata = {}
    with bag_info_path.open("r", encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                key, val = line.split(":", 1)
                metadata[key.strip()] = val.strip()
    return metadata


def parse_desc_metadata(xml_path: Path) -> dict[str, Any]:
    """Parse descriptive XML metadata using robust local name matching."""
    if not xml_path.exists():
        return {}

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception:
        return {}

    def find_text(xpath_tag: str) -> str | None:
        local_tag = xpath_tag.split("/")[-1]
        for candidate in root.iter():
            if candidate.tag.endswith(local_tag):
                return candidate.text
        return None

    doi = find_text("identifier")
    title = find_text("title")
    publication_year = find_text("publicationYear")
    production_year = find_text("productionYear")
    rights = find_text("controlledRights")

    # Find the identical-to source URL if present
    source_url = None
    for candidate in root.iter():
        if (
            candidate.tag.endswith("relatedIdentifier")
            and candidate.attrib.get("relatedIdentifierType") == "URL"
        ):
            source_url = candidate.text
            break
    if not source_url and doi:
        source_url = f"https://doi.org/{doi}"

    # Extract creators list
    creators = []
    for el in root.iter():
        if el.tag.endswith("creator"):
            name = None
            affiliation = None
            orcid = None
            for child in el:
                if child.tag.endswith("creatorName"):
                    name = child.text
                elif child.tag.endswith("creatorAffiliation"):
                    affiliation = child.text
                elif (
                    child.tag.endswith("nameIdentifier")
                    and child.attrib.get("nameIdentifierScheme") == "ORCID"
                ):
                    orcid = child.text
            if name:
                creators.append({"name": name, "affiliation": affiliation, "orcid": orcid})

    return {
        "title": title,
        "doi": doi,
        "publication_year": publication_year,
        "production_year": production_year,
        "rights": rights,
        "source_url": source_url,
        "creators": creators,
    }


def parse_tech_metadata(xml_path: Path) -> dict[str, Any]:
    """Parse technical XML metadata."""
    if not xml_path.exists():
        return {}

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception:
        return {}

    def find_text(tag_name: str) -> str | None:
        for candidate in root.iter():
            if candidate.tag.endswith(tag_name):
                return candidate.text
        return None

    archive_date = find_text("archiveDate")
    responsible_email = find_text("responsibleEmail")
    size_bytes = find_text("size")

    return {
        "archive_date": archive_date,
        "responsible_email": responsible_email,
        "size_bytes_technical": int(size_bytes) if size_bytes and size_bytes.isdigit() else None,
    }


def build_manifest(data_root: Path) -> DatasetManifest:
    generated_at_utc = utc_now_iso()
    file_inventory = build_inventory(data_root, generated_at_utc=generated_at_utc)

    # 1. Parse metadata files
    bag_info_path = data_root / "bag-info.txt"
    desc_xml_path = data_root / "data" / "descriptive-md" / "dataset.desc_md.xml"
    tech_xml_path = data_root / "data" / "technical-md" / "dataset.tech_md.xml"

    # Defensive fallback searches using rglob
    if data_root.exists():
        if not desc_xml_path.exists():
            desc_f = list(data_root.rglob("dataset.desc_md.xml"))
            if desc_f:
                desc_xml_path = desc_f[0]
        if not tech_xml_path.exists():
            tech_f = list(data_root.rglob("dataset.tech_md.xml"))
            if tech_f:
                tech_xml_path = tech_f[0]

    bag_info = parse_bag_info(bag_info_path)
    desc_meta = parse_desc_metadata(desc_xml_path)
    tech_meta = parse_tech_metadata(tech_xml_path)

    dataset_metadata = {
        "bag_info": bag_info,
        "descriptive": desc_meta,
        "technical": tech_meta,
    }

    # 2. Extract archive zip member counts without extraction
    extracted_file_counts = {}
    if data_root.exists():
        from mbp.audit.archives import inventory_zip_archives

        try:
            zip_members = inventory_zip_archives(data_root)
            counts = Counter(m.archive_name for m in zip_members)
            extracted_file_counts = dict(counts)
        except Exception:
            pass

    # Extract Archive-level metadata fields from BagIt manifest
    doi = desc_meta.get("doi")
    source = desc_meta.get("source_url")
    date_downloaded = bag_info.get("Bagging-Date")

    archive_inventory = build_archive_inventory(
        file_inventory,
        doi=doi,
        source=source,
        date_downloaded=date_downloaded,
        extracted_file_counts=extracted_file_counts,
    )

    provenance = Provenance(
        schema_version=SCHEMA_VERSION,
        generated_at_utc=generated_at_utc,
        tool_name="mbp audit manifest",
        tool_version=__version__,
        data_root_input=str(data_root),
        data_root_exists=data_root.exists(),
        preprocessing_commit=current_commit(Path.cwd()),
    )

    # 3. Assemble and return DatasetManifest
    return DatasetManifest(
        provenance=provenance,
        archive_inventory=archive_inventory,
        file_inventory=file_inventory,
        file_count=len(file_inventory),
        archive_count=len(archive_inventory),
        total_size_bytes=sum(record.size_bytes for record in file_inventory),
        row_count_by_file_family=row_counts_by_family(file_inventory),
        file_count_by_family=dict(Counter(record.file_family for record in file_inventory)),
        modality_file_count=modality_file_counts(file_inventory),
        expected_audit_requirements=EXPECTED_AUDIT_REQUIREMENTS,
        known_anomalies=[],
        audit_warnings=audit_warnings(data_root, file_inventory),
        dataset_metadata=dataset_metadata,
    )


def row_counts_by_family(records: list[FileInventoryRecord]) -> dict[str, int]:
    counts: defaultdict[str, int] = defaultdict(int)
    for record in records:
        if record.row_count is not None:
            counts[record.file_family] += record.row_count
    return dict(counts)


def modality_file_counts(records: list[FileInventoryRecord]) -> dict[str, int]:
    family_counts = Counter(record.file_family for record in records)
    return {family: family_counts.get(family, 0) for family in MODALITY_FAMILIES}


def audit_warnings(data_root: Path, records: list[FileInventoryRecord]) -> list[str]:
    warnings: list[str] = []
    if not data_root.exists():
        warnings.append("data_root does not exist; manifest contains no dataset file evidence")
        return warnings
    if not records:
        warnings.append("data_root exists but no files were found")
    missing_modalities = [
        family for family, count in modality_file_counts(records).items() if count == 0
    ]
    if missing_modalities:
        warnings.append("no files detected for modalities: " + ", ".join(missing_modalities))
    return warnings


def current_commit(cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None
