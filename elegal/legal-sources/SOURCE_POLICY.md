# E-LEGAL Authoritative Legal Source Policy

## Ingestion states

`DISCOVERED`  
A potential source has been identified.

`SOURCE_VERIFIED_METADATA`  
The official publisher, identifier, publication date and canonical source page have been verified.

`FULL_TEXT_ACQUIRED`  
The authoritative instrument/judgment bytes have been acquired from the permitted source.

`SOURCE_HASHED`  
The archived source bytes have an immutable cryptographic fingerprint.

`STRUCTURE_PARSED`  
Provisions/paragraphs and citations have been parsed.

`COMMENCEMENT_RESOLVED`  
Effective-date/commencement rules have been resolved from authoritative text.

`LEGAL_QA_VERIFIED`  
Human/approved legal QA has validated the structured representation.

`CURRENT_AUTHORITY_READY`  
The source may be used as a current authoritative node, subject to later treatment and temporal filters.

## Required rule

Metadata verification alone does not equal full legal ingestion.

Where the Gazette or President's Office confirms an instrument but full text has not yet been archived and parsed, the registry must preserve the distinction and use a pending state rather than inventing provision changes, source hashes or commencement dates.

## Source conflicts

If Gazette, MVLAW, court sources or another official source appear inconsistent:

`SOURCE_CONFLICT -> LEGAL_SOURCE_REVIEW_QUEUE`

E-LEGAL must never silently choose the newest indexed text.

## Effective dates

Store the authoritative commencement rule separately from any computed date. When wording such as "30 days from ratification and publication" applies, the raw rule must remain available and the computed date must be reviewable.

## Court treatment

Hearing notices, procedural listings and press reports are case events, not precedents. Precedent edges require an authoritative judgment/order and appropriate treatment analysis.
