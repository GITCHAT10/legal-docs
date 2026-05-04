# API Boundary Stubs

AEGIS:
- GET /aegis/session/introspect
- POST /aegis/sso/start
- POST /aegis/session/revoke

SHADOW:
- POST /shadow/events/interface
- GET /shadow/events
- GET /shadow/proof/{trace_id}

FCE:
- GET /fce/settlements
- POST /fce/payment-request
- GET /fce/tax-reports
- GET /fce/reconciliation/status

PRESTIGE:
- GET /prestige/search
- POST /prestige/quote/request
- POST /prestige/human-verify/request
- GET /prestige/logistics-seal/status

MAC EOS:
- GET /mac-eos/booking/status
- GET /mac-eos/property/{property_id}
- POST /mac-eos/booking/intent

UHA:
- GET /uha/courses
- GET /uha/student/progress
- POST /uha/enrollment/request
- GET /shadow/certificates/verify

ILUVIA:
- GET /iluvia/catalog
- GET /iluvia/community/feed
- POST /iluvia/community/post
- POST /iluvia/order/intent

BUILDX:
- GET /buildx/services
- POST /buildx/project-intake
- POST /buildx/site-assessment/request
- GET /buildx/project/status

UT:
- GET /ut/routes
- POST /ut/transfer/request
- GET /ut/logistics/status
- GET /ut/manifest/{trace_id}

SKYGODOWN:
- GET /skygodown/shipment/status
- POST /skygodown/quote/request
- GET /skygodown/landed-cost/{shipment_id}

iMOXON:
- POST /imoxon/procurement-request
- GET /imoxon/supplier/status
- GET /imoxon/order/status

eLEGAL:
- POST /elegal/public-question
- GET /elegal/public-question/status
- POST /elegal/expert-panel/route
- GET /shadow/legal-intake/proof

EXMAIL:
- POST /exmail/campaign/draft
- POST /exmail/notification/send
- GET /exmail/template/list

OCEANeX:
- GET /oceanex/batch/status
- GET /oceanex/factory/metrics
- GET /oceanex/impact/report

SKYFARM:
- GET /skyfarm/batch/status
- GET /skyfarm/market-signal
- GET /skyfarm/esg/proof
