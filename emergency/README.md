# MNOS emergency dispatch simulation and Brain Coral advisory contract

This is an isolated engineering prototype. It is **not connected to live SOS inputs, telephony, responders, hospitals, or production APIs**. No AI score may suppress or delay a reported emergency. Brain Coral can display an A0 case projection only; it cannot acknowledge, assign, dispatch, cancel, close, or triage a case.

The MNOS kernel uses SQLite for simulated idempotent reports, versioned state transitions, assigned responder checks, facility handoff, and a local history. It accepts actor dictionaries from a trusted test harness only; it does not authenticate callers. The Brain Coral TypeScript projection exposes case state without patient details or mutation methods.

Run `python -m unittest emergency.test_mnos_dispatch -v` from the MNOS repository root. Run `npx vitest run emergency/brainCoralAdvisory.test.ts` from the Brain Coral repository root.

Before any live connection: replace placeholder AEGIS direct signature acceptance and development secret fallback; add authenticated patient/dispatcher/responder identities, scoped incident permissions, encrypted durable storage and verified audit, protected and acknowledged notification channels, manual fallback, location accuracy and land/sea/air travel-time tests, clinical governance, independent security review, simulation UAT, rollback and dual sign-off. No third-party repository code has been copied; project ideas inspired the interface only. Project Ears remains unverified.
