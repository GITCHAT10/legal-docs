# Prestige Holidays Core - API Map

All routes are prefixed with `/api/v1`.

## Reservations & Rooms (`/reservations`)
- `POST /`: Create booking (Validated for capacity & room status).
- `GET /rooms`: List room inventory and status.
- `POST /rooms`: Onboard new room inventory.

## Guests (`/guests`)
- `POST /`: Register guest.
- `GET /`: Search/List guest profiles.

## Finance (`/finance`)
- `POST /folios`: Open new folio for reservation.
- `POST /folios/{id}/charges`: Post Maldives-taxed charge (10% SC, 17% TGST).
- `POST /folios/{id}/payments`: Record payment.
- `POST /folios/{id}/finalize`: Authoritative invoice generation.

## Transfers (`/transfers`)
- `POST /`: Create transfer request.
- `POST /requests/{id}/assign`: Assign vehicle (Validated for type & status).
- `PUT /requests/{id}/manifest`: Authoritative guest manifest update.

## Maintenance (`/maintenance`)
- `POST /`: Create ticket (P1/P2/CRITICAL blocks room).
- `PUT /{id}`: Lifecycle update (CLOSED releases room to READY).

## Intake Engine (`/staging`)
- `POST /upload`: Bulk XLSX upload for rooming lists.
- `POST /promote-bulk`: Authoritative promotion of staged records to live reservations.
