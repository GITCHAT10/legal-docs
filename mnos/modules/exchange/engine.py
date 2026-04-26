import uuid
from datetime import datetime, UTC

class ExchangeEngine:
    def __init__(self, core):
        self.core = core
        self.listings = {}
        self.bids = {}

    def list_asset(self, actor_ctx: dict, asset_data: dict):
        return self.core.execute_commerce_action(
            "exchange.asset.list",
            actor_ctx,
            self._internal_list,
            asset_data
        )

    def _internal_list(self, data):
        asset_id = f"ASSET-{uuid.uuid4().hex[:6].upper()}"
        listing = {
            "asset_id": asset_id,
            "owner_did": self.core.guard.get_actor().get("identity_id"),
            "description": data.get("description"),
            "starting_price": data.get("price"),
            "status": "LISTED",
            "created_at": datetime.now(UTC).isoformat()
        }
        self.listings[asset_id] = listing
        self.core.events.publish("exchange.asset_listed", listing)
        return listing

    def place_bid(self, actor_ctx: dict, asset_id: str, bid_amount: float):
        return self.core.execute_commerce_action(
            "exchange.asset.bid",
            actor_ctx,
            self._internal_bid,
            asset_id, bid_amount
        )

    def _internal_bid(self, asset_id, amount):
        if asset_id not in self.listings:
            raise ValueError("Asset not found")
        bid = {
            "bid_id": uuid.uuid4().hex[:6],
            "asset_id": asset_id,
            "bidder_did": self.core.guard.get_actor().get("identity_id"),
            "amount": amount,
            "timestamp": datetime.now(UTC).isoformat()
        }
        if asset_id not in self.bids: self.bids[asset_id] = []
        self.bids[asset_id].append(bid)
        self.core.events.publish("exchange.bid_placed", bid)
        return bid

    def finalize_exchange(self, actor_ctx: dict, asset_id: str, winning_bid_id: str):
        return self.core.execute_commerce_action(
            "exchange.asset.finalize",
            actor_ctx,
            self._internal_finalize,
            asset_id, winning_bid_id
        )

    def _internal_finalize(self, asset_id, bid_id):
        asset = self.listings.get(asset_id)
        winning_bid = next((b for b in self.bids.get(asset_id, []) if b["bid_id"] == bid_id), None)
        if not winning_bid: raise ValueError("Invalid Bid")

        # Escrow and Transfer
        escrow_res = self.core.fce.process_clearing_settlement(winning_bid["amount"], {"seller": 0.90, "platform": 0.10})

        old_owner = asset["owner_did"]
        asset["owner_did"] = winning_bid["bidder_did"]
        asset["status"] = "TRANSFERRED"

        transfer_record = {
            "asset_id": asset_id,
            "from": old_owner,
            "to": asset["owner_did"],
            "bid_amount": winning_bid["amount"],
            "escrow": escrow_res
        }

        self.core.shadow.commit("exchange.ownership_transfer", winning_bid["bidder_did"], transfer_record)
        self.core.events.publish("exchange.transfer_finalized", transfer_record)
        return transfer_record

    def transfer_asset(self, actor_ctx: dict, transfer_data: dict):
        return self.core.execute_commerce_action(
            "exchange.asset.transfer",
            actor_ctx,
            self._internal_transfer,
            transfer_data
        )

    def _internal_transfer(self, data):
        transfer = {
            "transfer_id": f"EX-{uuid.uuid4().hex[:6].upper()}",
            "asset_id": data.get("asset_id"),
            "seller_id": data.get("seller_id"),
            "buyer_id": self.core.guard.get_actor().get("identity_id"),
            "price": data.get("price"),
            "status": "FINALIZED"
        }
        self.core.events.publish("exchange.transfer_completed", transfer)
        return transfer
