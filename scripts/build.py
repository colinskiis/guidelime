#!/usr/bin/env python3
"""
Guidelime Build Script

Scans guideline markdown files, validates them, and generates JSON indexes.
Uses only Python standard library - no external dependencies.

Usage:
    python scripts/build.py
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Required fields for validation
REQUIRED_FIELDS = [
    'id', 'title', 'organization', 'url', 'specialty',
    'publication_date', 'status', 'guideline_type', 'open_access'
]

# Valid values for controlled fields
VALID_STATUS = ['current', 'superseded', 'withdrawn']
VALID_GUIDELINE_TYPES = ['clinical-practice', 'consensus', 'position-paper', 'expert-opinion', 'screening']
VALID_SPECIALTIES = [
    'cardiology', 'infectious-disease', 'oncology', 'endocrinology',
    'neurology', 'pulmonology', 'gastroenterology', 'nephrology',
    'rheumatology', 'hematology', 'pediatrics', 'obstetrics-gynecology',
    'psychiatry', 'emergency-critical-care', 'general-preventive',
    'urology', 'dermatology', 'ophthalmology', 'otolaryngology',
    'geriatrics', 'radiology', 'sleep-medicine', 'hepatology',
    'orthopedics', 'pain-medicine', 'surgical-care', 'colorectal-surgery',
    'trauma-surgery', 'nutrition', 'addiction-medicine',
    'allergy-immunology', 'anesthesiology', 'critical-care'
]


def parse_yaml_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parse YAML frontmatter from markdown content.
    Returns (metadata dict, remaining content).
    """
    if not content.startswith('---'):
        return {}, content

    # Find the closing ---
    end_match = re.search(r'\n---\s*\n', content[3:])
    if not end_match:
        return {}, content

    yaml_content = content[3:end_match.start() + 3]
    remaining = content[end_match.end() + 3:]

    # Parse the YAML
    metadata = {}
    current_key = None
    current_list = None

    for line in yaml_content.split('\n'):
        # Skip empty lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Check for list item
        if line.startswith('  - ') or line.startswith('  #'):
            if current_list is not None and not line.strip().startswith('#'):
                value = line.strip()[2:].strip()  # Remove "- "
                if value:
                    current_list.append(parse_yaml_value(value))
            continue

        # Check for key: value
        match = re.match(r'^(\w+):\s*(.*)', line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()

            if value == '' or value.startswith('#'):
                # Could be a list or empty value
                metadata[key] = []
                current_key = key
                current_list = metadata[key]
            else:
                metadata[key] = parse_yaml_value(value)
                current_key = key
                current_list = None

    # Clean up empty lists
    for key in list(metadata.keys()):
        if metadata[key] == []:
            metadata[key] = None

    return metadata, remaining


def parse_yaml_value(value: str) -> Any:
    """Parse a YAML value string into Python type."""
    # Remove quotes if present
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]

    # Check for null
    if value.lower() in ('null', '~', ''):
        return None

    # Check for boolean
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False

    # Check for number
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    # Return as string
    return value


def validate_guideline(metadata: dict, filepath: Path) -> list[str]:
    """Validate a guideline's metadata. Returns list of error messages."""
    errors = []

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in metadata or metadata[field] is None:
            errors.append(f"Missing required field: {field}")

    # Validate controlled vocabularies
    if 'status' in metadata and metadata['status'] not in VALID_STATUS:
        errors.append(f"Invalid status '{metadata['status']}'. Must be one of: {VALID_STATUS}")

    if 'guideline_type' in metadata and metadata['guideline_type'] not in VALID_GUIDELINE_TYPES:
        errors.append(f"Invalid guideline_type '{metadata['guideline_type']}'. Must be one of: {VALID_GUIDELINE_TYPES}")

    if 'specialty' in metadata and metadata['specialty'] not in VALID_SPECIALTIES:
        errors.append(f"Invalid specialty '{metadata['specialty']}'. Must be one of: {VALID_SPECIALTIES}")

    # Validate specialty matches directory
    expected_specialty = filepath.parent.name
    if 'specialty' in metadata and metadata['specialty'] != expected_specialty:
        errors.append(f"Specialty '{metadata['specialty']}' doesn't match directory '{expected_specialty}'")

    return errors


def generate_warnings(metadata: dict, filepath: Path, root: Path) -> list[str]:
    """Generate warnings for a guideline. Returns list of warning messages."""
    warnings = []

    # Check for stale last_reviewed
    if 'last_reviewed' in metadata and metadata['last_reviewed']:
        try:
            reviewed = datetime.strptime(str(metadata['last_reviewed']), '%Y-%m-%d')
            days_old = (datetime.now() - reviewed).days
            if days_old > 365:
                warnings.append(f"Last reviewed {days_old} days ago - may need review")
        except ValueError:
            pass

    # Check for missing PDF if has_pdf is True
    if metadata.get('has_pdf') and metadata.get('pdf_path'):
        pdf_full_path = root / metadata['pdf_path']
        if not pdf_full_path.exists():
            warnings.append(f"PDF not found: {metadata['pdf_path']}")

    return warnings


def build_indexes(guidelines: list[dict]) -> dict[str, Any]:
    """Build all index structures from guidelines list."""
    # all.json - complete flattened index
    all_index = {
        'generated': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'count': len(guidelines),
        'guidelines': guidelines
    }

    # by-specialty.json
    by_specialty = {}
    for g in guidelines:
        spec = g.get('specialty', 'unknown')
        if spec not in by_specialty:
            by_specialty[spec] = []
        by_specialty[spec].append(g['id'])

    # by-organization.json
    by_organization = {}
    for g in guidelines:
        org = g.get('organization', 'Unknown')
        if org not in by_organization:
            by_organization[org] = []
        by_organization[org].append(g['id'])

    # by-condition.json
    by_condition = {}
    for g in guidelines:
        conditions = g.get('conditions') or []
        for cond in conditions:
            if cond not in by_condition:
                by_condition[cond] = []
            by_condition[cond].append(g['id'])

    return {
        'all.json': all_index,
        'by-specialty.json': by_specialty,
        'by-organization.json': by_organization,
        'by-condition.json': by_condition
    }


def main():
    # Determine root directory
    script_dir = Path(__file__).parent
    root = script_dir.parent

    guidelines_dir = root / 'guidelines'
    index_dir = root / '_index'

    if not guidelines_dir.exists():
        print(f"Error: guidelines directory not found at {guidelines_dir}")
        sys.exit(1)

    # Collect all guidelines
    guidelines = []
    all_errors = []
    all_warnings = []

    # Find all .md files in guidelines directory
    md_files = list(guidelines_dir.glob('**/*.md'))

    print(f"Found {len(md_files)} guideline files")
    print("-" * 50)

    for filepath in sorted(md_files):
        relative_path = filepath.relative_to(root)

        # Read and parse
        content = filepath.read_text(encoding='utf-8')
        metadata, _ = parse_yaml_frontmatter(content)

        if not metadata:
            all_errors.append((relative_path, ["No valid YAML frontmatter found"]))
            continue

        # Validate
        errors = validate_guideline(metadata, filepath)
        warnings = generate_warnings(metadata, filepath, root)

        if errors:
            all_errors.append((relative_path, errors))
        if warnings:
            all_warnings.append((relative_path, warnings))

        # If valid, add to guidelines list
        if not errors:
            # Add file_path to metadata
            metadata['file_path'] = str(relative_path)
            guidelines.append(metadata)
            print(f"  [OK] {relative_path}")
        else:
            print(f"  [ERROR] {relative_path}")

    print("-" * 50)

    # Report errors
    if all_errors:
        print(f"\nErrors ({len(all_errors)} files):")
        for filepath, errors in all_errors:
            print(f"\n  {filepath}:")
            for err in errors:
                print(f"    - {err}")

    # Report warnings
    if all_warnings:
        print(f"\nWarnings ({len(all_warnings)} files):")
        for filepath, warnings in all_warnings:
            print(f"\n  {filepath}:")
            for warn in warnings:
                print(f"    - {warn}")

    # Generate indexes
    if guidelines:
        print(f"\nGenerating indexes for {len(guidelines)} valid guidelines...")

        index_dir.mkdir(exist_ok=True)
        indexes = build_indexes(guidelines)

        for filename, data in indexes.items():
            output_path = index_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  Created: {output_path.relative_to(root)}")
    else:
        print("\nNo valid guidelines found. Indexes not generated.")

    print("\nDone!")

    # Exit with error code if there were errors
    if all_errors:
        sys.exit(1)


if __name__ == '__main__':
    main()
