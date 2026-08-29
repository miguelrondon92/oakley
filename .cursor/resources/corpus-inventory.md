# Oakley Corpus Inventory

Catalog of source PDFs for Oakwood Glen HOA (Harris County, TX) MVP.

## HOA bylaws (`bylaws/` — source_type: `hoa_bylaw`)

| source_file | document_title | notes |
|-------------|----------------|-------|
| `Recorded-OAKWOOD-GLEN-SECOND-AMENDED-AND-RESTATED-BYLAWS-03782964xC3D0.pdf` | Oakwood Glen Bylaws (Second Amended and Restated) | Primary governing document (~1.1 MB) |
| `ACC-Denial-Letter-and-Appeal-Hearing-Policy_REAL-PROPERTY_2021.pdf` | ACC Denial Letter and Appeal Hearing Policy | Architectural Control Committee |
| `Deed-Restriction-Violation-Hearing-Policy_REAL-PROPERTY_2021.pdf` | Deed Restriction Violation Hearing Policy | Violation hearings |
| `Large-Contract-Bid-Solicitation-Policy_REAL-PROPERTY_2021.pdf` | Large Contract Bid Solicitation Policy | Contract bidding |
| `OGA-Architectural-Review-Authority-Appointment-Policy-02573519xC3D0C.pdf` | OGA Architectural Review Authority Appointment Policy | OGA / architectural review |
| `Religious-Display-Policy_REAL-PROPERTY_2021.pdf` | Religious Display Policy | |
| `Security-Measures-Policy_REAL-PROPERTY_2021.pdf` | Security Measures Policy | |
| `Swimming-Pool-Enclosure-Policy_REAL-PROPERTY_2021.pdf` | Swimming Pool Enclosure Policy | |

## County regulations (`county_regulations/` — source_type: `county_regulation`)

| source_file | document_title | notes |
|-------------|----------------|-------|
| `Harris County Community Protections.pdf` | Harris County Community Protections | County code / protections |
| `Harris County Streets and Roads.pdf` | Harris County Streets and Roads | County streets and roads regulations (~2.2 MB) |

## Ingestion notes

- All paths are relative to `oakley/` repo root.
- `document_title` in chunk metadata should match this table unless a clearer title is extracted from the PDF cover page.
- When users ask HOA-only questions, RAG/CLI may filter `source_type=hoa_bylaw`.
- When users ask county questions, filter `source_type=county_regulation`.
- Cross-jurisdiction questions (e.g. pool rules vs county code) may search both without filter.

## Future expansion

Add rows here before ingesting new jurisdictions. Update Vector Store and QA fixtures when corpus grows.
