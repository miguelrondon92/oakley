# Oakley Corpus Inventory

Catalog of source documents for Oakwood Glen HOA (Harris County, TX).

Paths are relative to `oakley/` repo root. `ingest_version` 2+ uses `hoa_docs/` layout.

## HOA bylaws (`hoa_docs/bylaws/` — source_type: `hoa_bylaw`, doc_category: `bylaws`)

| source_file | document_title | notes |
|-------------|----------------|-------|
| `Recorded-OAKWOOD-GLEN-SECOND-AMENDED-AND-RESTATED-BYLAWS-03782964xC3D0.pdf` | Oakwood Glen Bylaws (Second Amended and Restated) | Primary governing document |
| `ACC-Denial-Letter-and-Appeal-Hearing-Policy_REAL-PROPERTY_2021.pdf` | ACC Denial Letter and Appeal Hearing Policy | Architectural Control Committee |
| `Deed-Restriction-Violation-Hearing-Policy_REAL-PROPERTY_2021.pdf` | Deed Restriction Violation Hearing Policy | Violation hearings |
| `Large-Contract-Bid-Solicitation-Policy_REAL-PROPERTY_2021.pdf` | Large Contract Bid Solicitation Policy | Contract bidding |
| `OGA-Architectural-Review-Authority-Appointment-Policy-02573519xC3D0C.pdf` | OGA Architectural Review Authority Appointment Policy | OGA / architectural review |
| `Religious-Display-Policy_REAL-PROPERTY_2021.pdf` | Religious Display Policy | |
| `Security-Measures-Policy_REAL-PROPERTY_2021.pdf` | Security Measures Policy | |
| `Swimming-Pool-Enclosure-Policy_REAL-PROPERTY_2021.pdf` | Swimming Pool Enclosure Policy | |

## HOA policies (`hoa_docs/policies/` — doc_category: `policies`)

| source_file | document_title |
|-------------|----------------|
| `Amendment-to-Collection-Policy.pdf` | Amendment to Collection Policy |
| `Candidate-Form-2024.pdf` | Candidate Form 2024 |
| `Collection-Policy.pdf` | Collection Policy |
| `Conflict-of-Interest-Policy-RP-2016-302394.pdf` | Conflict of Interest Policy |
| `Notice-of-Association-Policies-20110545794.pdf` | Notice of Association Policies |
| `Oakwood-Glen-Amended-Deed-recorded-01147298xC3D0C.pdf` | Oakwood Glen Amended Deed |
| `Oakwood-Glen-Amended-Deed-recorded-01147298xC3D0C (1).pdf` | Oakwood Glen Amended Deed |
| `Policy-Regarding-Operation-of-a-Business-out-of-a-Home-Recorded.pdf` | Policy Regarding Operation of a Business out of a Home |
| `RP-2017-283716-Email-Policy-Recorded-01128679xC3D0C.pdf` | Email Policy |
| `RP-2017-283767-Board-Resolution-Recorded-01128676xC3D0C.pdf` | Board Resolution |
| `RP-2017-283779-Electric-Generators-Regulation-Recorded-01128692xC3D0C.pdf` | Electric Generators Regulation |
| `Recorded-Oakwood-Glen-Forced-Mow-Policy-01360517xC3D0C.pdf` | Forced Mow Policy |
| `Recorded-Oakwood-Glen-Operating-Reserve-Policy-01510621xC3D0C-1.pdf` | Operating Reserve Policy |
| `Records-Production-Policy-20110545796.pdf` | Records Production Policy |
| `Records-Retention-Policy-20110545798.pdf` | Records Retention Policy |
| `Section-202.006-Affidavit-20110545795.pdf` | Section 202.006 Affidavit |

## Deed restrictions (`hoa_docs/policies/deed_restrictions/` — doc_category: `deed_restrictions`)

| source_file | document_title | notes |
|-------------|----------------|-------|
| `Deed-Restrictions-Section-1.pdf` | Deed Restrictions Section 1 | PDF chunks carry companion metadata from `deed_restrictions.md` |
| `Deed-Restrictions-Section-2.pdf` | Deed Restrictions Section 2 | |
| `deed_restrictions.md` | Deed Restrictions Overview | Indexed as searchable markdown chunks |

## FAQs (`hoa_docs/faqs/` — doc_category: `faqs`)

| source_file | document_title |
|-------------|----------------|
| `faqs.md` | Frequently Asked Questions |

## County regulations (`county_regulations/` — source_type: `county_regulation`, doc_category: `county`)

| source_file | document_title | notes |
|-------------|----------------|-------|
| `Harris County Community Protections.pdf` | Harris County Community Protections | County code / protections |
| `Harris County Streets and Roads.pdf` | Harris County Streets and Roads | County streets and roads regulations |

## Ingestion notes

- `document_title` in chunk metadata should match this table unless a clearer title is extracted from the PDF cover page.
- When users ask HOA-only questions, RAG/CLI may filter `source_type=hoa_bylaw`.
- When users ask county questions, filter `source_type=county_regulation`.
- Legacy root `bylaws/` paths are obsolete; moved files reuse chunks by content hash on incremental parse.

## Future expansion

Add rows here before ingesting new jurisdictions. Update Vector Store and QA fixtures when corpus grows.
