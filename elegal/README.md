# E-LEGAL — Maldives Legal Intelligence

E-LEGAL is the Maldives-specific sovereign legal operating system owned by Maldives International Group Pvt Ltd (MIG), with the Artificial Intelligence Group providing the AI and technology layer under the MIG brand.

This directory is the canonical repository location for E-LEGAL legal-intelligence baselines and authoritative-source ingestion metadata.

## Current engineering status

- EF-01 — Identity, conflicts, escrow and bank abstraction: architecture locked
- EF-02 — Financial integrity, KYC/AML and recovery: architecture locked
- EF-03 — Cloud trust, encryption, tenancy and human authority: architecture locked
- EF-04 — ICMS/MIRA/Virtual Chambers adapters: architecture locked
- EF-05 — Maldives Legal Intelligence Core: bootstrapped in this repository

## EF-05 authority order

1. Official Government Gazette / enacted instrument
2. Official consolidated legislation (MVLAW)
3. Official Supreme Court / High Court / authorized court sources
4. Official regulator or government material
5. Official translations
6. Unofficial translations
7. Secondary commentary

Publication authority, legal hierarchy and judicial precedent force are stored separately.

## Current source registry

The initial production bootstrap is:

- `legal-sources/registry/2026-08-31.yaml`

It records the Maldives instruments published on 31 August 2026 with source URLs, commencement status, practice-area impact and ingestion state.

## Safety invariants

E-LEGAL AI is A0 decision-support only. It may research, summarize, compare, translate, analyze and draft. It may not sign, file, submit, notarize, certify, authorize funds, waive conflicts or impersonate a lawyer, judge, notary or authorized human.

A legal instrument is never considered fully ingested solely because its metadata is known. Source metadata verification, authoritative full-text acquisition, source hashing, provision parsing, commencement resolution and legal QA are separate states.
