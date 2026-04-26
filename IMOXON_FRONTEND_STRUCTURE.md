# iMOXON Frontend Structure (Flutter / Web)

## Core App (Bubble OS)
- **App Engine**: Manages local state and SDK bindings.
- **Identity Bridge**: Integrates eFaas and AEGIS tokens.

## Marketplace (B2C)
- `lib/ui/marketplace/`: Listing view, Search, Categories.
- `lib/ui/checkout/`: Multi-leg checkout, Installment selector.

## Merchant Hub (B2B)
- `lib/ui/merchant/`: Inventory management, Payout dashboard.
- `lib/ui/pos/`: BPE integrated point-of-sale interface.

## Wallet & Tourism
- `lib/ui/wallet/`: Transaction history, QR payment.
- `lib/ui/tourism/`: Booking cards for transfers and excursions.

## Style Guide
- **Theming**: Tailwind CSS inspired (Web) / Material 3 (Flutter).
- **Icons**: Lucide/Feather icons for clarity.
