# Guidelime

A structured repository of medical research guidelines - a virtual rolodex optimized for both human browsing and LLM consumption.

## Structure

```
guidelime/
├── guidelines/           # Guideline metadata files (.md)
│   ├── cardiology/
│   ├── infectious-disease/
│   └── ...
├── pdfs/                 # Optional PDF storage
├── _index/               # Auto-generated JSON indexes
├── _templates/           # Template for new entries
└── scripts/              # Build tools
```

## Adding a Guideline

1. Copy the template:
   ```bash
   cp _templates/guideline.md guidelines/[specialty]/[id].md
   ```

2. Fill in the metadata (see fields below)

3. Run the build script:
   ```bash
   python scripts/build.py
   ```

## Guideline Fields

### Required
| Field | Description | Example |
|-------|-------------|---------|
| `id` | Unique slug | `aha-heart-failure-2022` |
| `title` | Full official title | `2022 AHA/ACC/HFSA Guideline...` |
| `organization` | Primary issuing body | `American Heart Association` |
| `url` | Official URL | `https://...` |
| `specialty` | Must match directory name | `cardiology` |
| `publication_date` | YYYY-MM-DD | `2022-04-01` |
| `status` | `current`, `superseded`, or `withdrawn` | `current` |
| `guideline_type` | Type of document | `clinical-practice` |
| `open_access` | Is it freely available? | `true` |

### Optional
| Field | Description |
|-------|-------------|
| `short_title` | Shorter display name |
| `collaborators` | List of co-publishing organizations |
| `country` | ISO 2-letter country code |
| `doi` | Digital Object Identifier |
| `pmid` | PubMed ID |
| `evidence_system` | Grading system (GRADE, AHA, etc.) |
| `conditions` | List of medical conditions covered |
| `tags` | Searchable keywords |
| `previous_version_date` | When prior guideline was published |
| `supersedes` | ID of previous version |
| `superseded_by` | ID of newer version (if outdated) |
| `pdf_path` | Relative path to local PDF |
| `has_pdf` | Boolean - is PDF stored locally? |
| `last_reviewed` | When you verified this entry is current |

### Guideline Types
- `clinical-practice` - Evidence-based clinical practice guideline
- `consensus` - Consensus statement from expert panel
- `position-paper` - Society position paper
- `expert-opinion` - Expert opinion/recommendation

## JSON Indexes

The build script generates these indexes in `_index/`:

- **all.json** - Complete metadata for all guidelines (for LLM consumption)
- **by-specialty.json** - Guidelines grouped by medical specialty
- **by-organization.json** - Guidelines grouped by issuing organization
- **by-condition.json** - Guidelines grouped by medical condition

## Specialties

- cardiology
- infectious-disease
- oncology
- endocrinology
- neurology
- pulmonology
- gastroenterology
- nephrology
- rheumatology
- hematology
- pediatrics
- obstetrics-gynecology
- psychiatry
- emergency-critical-care
- general-preventive
