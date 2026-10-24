"""Fail-closed verifier for x402 Foundation's EIP-712 offer/receipt extension.

This module verifies seller-signed claims against a separately collected ledger
transfer. It does not infer a purchase from an address match. Service-key
authorization is supplied as retained evidence by the caller; a signature alone
does not establish that a key represents a resource.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from eth_account import Account
from eth_account.messages import encode_typed_data

FINALITY = {"SAFE", "FINAL"}
BASE_NETWORK = "eip155:8453"
BASE_CHAIN_ID = 8453
BASE_USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"

OFFER_TYPES = {
    "EIP712Domain": [
        {"name": "name", "type": "string"},
        {"name": "version", "type": "string"},
        {"name": "chainId", "type": "uint256"},
    ],
    "Offer": [
        {"name": "version", "type": "uint256"},
        {"name": "resourceUrl", "type": "string"},
        {"name": "scheme", "type": "string"},
        {"name": "network", "type": "string"},
        {"name": "asset", "type": "string"},
        {"name": "payTo", "type": "string"},
        {"name": "amount", "type": "string"},
        {"name": "validUntil", "type": "uint256"},
    ],
}
RECEIPT_TYPES = {
    "EIP712Domain": OFFER_TYPES["EIP712Domain"],
    "Receipt": [
        {"name": "version", "type": "uint256"},
        {"name": "network", "type": "string"},
        {"name": "resourceUrl", "type": "string"},
        {"name": "payer", "type": "string"},
        {"name": "issuedAt", "type": "uint256"},
        {"name": "transaction", "type": "string"},
    ],
}


def _typed(artifact: dict[str, Any], kind: str) -> tuple[dict[str, Any], str]:
    if artifact.get("format") != "eip712":
        raise ValueError("only the specified eip712 artifact format is supported")
    payload = artifact.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("EIP-712 artifact payload is missing")
    if kind == "offer":
        required = ("version", "resourceUrl", "scheme", "network", "asset", "payTo", "amount")
        if any(k not in payload for k in required):
            raise ValueError("offer is missing a required signed field")
        if payload["version"] != 1:
            raise ValueError("unsupported offer version")
        if set(payload) - set(required) - {"validUntil"}:
            raise ValueError("unsupported signed offer fields")
        msg = dict(payload)
        msg["validUntil"] = int(payload.get("validUntil") or 0)
        primary, domain_name, fields = "Offer", "x402 offer", OFFER_TYPES["Offer"]
    elif kind == "receipt":
        required = ("version", "network", "resourceUrl", "payer", "issuedAt")
        if any(k not in payload for k in required):
            raise ValueError("receipt is missing a required signed field")
        if payload["version"] != 1:
            raise ValueError("unsupported receipt version")
        if set(payload) - set(required) - {"transaction"}:
            raise ValueError("unsupported signed receipt fields")
        msg = dict(payload)
        msg["transaction"] = payload.get("transaction") or ""
        primary, domain_name, fields = "Receipt", "x402 receipt", RECEIPT_TYPES["Receipt"]
    else:
        raise ValueError("unknown artifact kind")
    # The EIP-712 schema is fixed by x402; use only its canonical fields.
    msg = {item["name"]: msg[item["name"]] for item in fields}
    full = {
        "types": {"EIP712Domain": OFFER_TYPES["EIP712Domain"], primary: fields},
        "primaryType": primary,
        "domain": {"name": domain_name, "version": "1", "chainId": 1},
        "message": msg,
    }
    signature = artifact.get("signature")
    if not isinstance(signature, str) or not signature.startswith("0x") or len(signature) != 132:
        raise ValueError("expected 65-byte 0x-prefixed EIP-712 signature")
    return full, signature


def recover_signer(artifact: dict[str, Any], kind: str) -> str:
    """Recover signer address from a canonical x402 EIP-712 offer or receipt."""
    full, signature = _typed(artifact, kind)
    return Account.recover_message(encode_typed_data(full_message=full), signature=signature).lower()


def _hash_evidence(obj: Any) -> str:
    body = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(body).hexdigest()


def verify_purchase(evidence: dict[str, Any], *, timestamp_tolerance_seconds: int = 86_400) -> dict[str, Any]:
    """Verify a signed offer + signed receipt against one finalized transfer.

    `authorization` must identify a signer authorized for this exact resource and
    include a reproducible source reference (for example an archived DID/DNS key
    binding). `settlement` must come from a chain-verified transfer collector.
    The function deliberately does not fetch network data or resolve identities.
    """
    contradictions: list[str] = []
    missing: list[str] = []
    resource = evidence.get("resource") or {}
    offer = evidence.get("offer") or {}
    receipt = evidence.get("receipt") or {}
    settlement = evidence.get("settlement") or {}
    authorization = evidence.get("authorization") or {}
    resource_url = resource.get("resource_url")
    try:
        offer_payload = offer.get("payload") or {}
        receipt_payload = receipt.get("payload") or {}
        offer_signer = recover_signer(offer, "offer")
    except Exception as exc:
        offer_signer = None
        contradictions.append(f"offer signature/format invalid: {type(exc).__name__}: {exc}")
        offer_payload = offer.get("payload") or {}
    try:
        receipt_signer = recover_signer(receipt, "receipt")
    except Exception as exc:
        receipt_signer = None
        contradictions.append(f"receipt signature/format invalid: {type(exc).__name__}: {exc}")
        receipt_payload = receipt.get("payload") or {}

    if not resource_url:
        missing.append("expected resource URL from retained Bazaar observation")
    if not settlement:
        missing.append("ledger-confirmed transfer and finality evidence")
    if not authorization.get("evidence_ref"):
        missing.append("retained resource-to-signing-key authorization evidence")
    if not authorization.get("signer"):
        missing.append("authorized signer identity")
    auth_document = authorization.get("evidence")
    if not isinstance(auth_document, dict) or not auth_document:
        missing.append("retained authorization source document")
    elif auth_document.get("resource_url") != resource_url or str(auth_document.get("signer", "")).lower() != str(authorization.get("signer", "")).lower():
        contradictions.append("retained authorization document does not bind the supplied resource and signer")
    if authorization.get("verified") is not True:
        missing.append("independently reviewed resource signer authorization")

    if resource_url:
        if offer_payload.get("resourceUrl") != resource_url:
            contradictions.append("signed offer resource URL does not match expected Bazaar resource")
        if receipt_payload.get("resourceUrl") != resource_url:
            contradictions.append("signed receipt resource URL does not match expected Bazaar resource")
    if offer_payload.get("scheme") != "exact":
        contradictions.append("only the x402 exact scheme is supported by this verifier")
    if offer_payload.get("network") != BASE_NETWORK or receipt_payload.get("network") != BASE_NETWORK:
        contradictions.append("signed artifact network is not Base mainnet CAIP-2 eip155:8453")
    if str(offer_payload.get("asset", "")).lower() != BASE_USDC:
        contradictions.append("signed offer does not use the approved canonical Base USDC contract")

    auth_signer = str(authorization.get("signer") or "").lower()
    auth_resource = authorization.get("resource_url")
    if auth_resource and resource_url and auth_resource != resource_url:
        contradictions.append("signer authorization applies to a different resource URL")
    if offer_signer and auth_signer and offer_signer != auth_signer:
        contradictions.append("offer signer is not the retained authorized resource signer")
    if receipt_signer and auth_signer and receipt_signer != auth_signer:
        contradictions.append("receipt signer is not the retained authorized resource signer")
    if offer_signer and receipt_signer and offer_signer != receipt_signer:
        contradictions.append("offer and receipt were signed by different addresses")

    if settlement:
        if int(settlement.get("chain_id", -1)) != BASE_CHAIN_ID:
            contradictions.append("settlement chain ID is not Base mainnet 8453")
        if str(settlement.get("finality", "")).upper() not in FINALITY:
            missing.append("safe/final transaction status")
        tx_hash = str(settlement.get("transaction_hash", "")).lower()
        if not tx_hash or tx_hash != str(receipt_payload.get("transaction", "")).lower():
            contradictions.append("signed receipt transaction hash does not match verified settlement")
        transfer = settlement.get("transfer") or {}
        for label, actual, expected in (
            ("payer", transfer.get("from"), receipt_payload.get("payer")),
            ("recipient", transfer.get("to"), offer_payload.get("payTo")),
            ("asset", transfer.get("asset"), offer_payload.get("asset")),
            ("base-unit amount", transfer.get("amount_base"), offer_payload.get("amount")),
        ):
            if actual is None:
                missing.append(f"verified token-transfer {label}")
            elif expected is None or str(actual).lower() != str(expected).lower():
                contradictions.append(f"settlement {label} does not match signed x402 evidence")
        receipt_payer = str(receipt_payload.get("payer", "")).lower()
        if transfer.get("from") and str(transfer["from"]).lower() != receipt_payer:
            contradictions.append("signed receipt payer does not match ERC-20 Transfer.from")
        block_time = settlement.get("block_time")
        issued_at = receipt_payload.get("issuedAt")
        valid_until = offer_payload.get("validUntil") or 0
        if valid_until and block_time:
            try:
                block_epoch_for_expiry = int(datetime.fromisoformat(str(block_time).replace("Z", "+00:00")).timestamp())
                if block_epoch_for_expiry > int(valid_until):
                    contradictions.append("signed offer expired before settlement")
            except (ValueError, TypeError, OverflowError):
                contradictions.append("invalid signed offer expiry")
        if block_time is not None and issued_at is not None:
            try:
                block_epoch = int(datetime.fromisoformat(str(block_time).replace("Z", "+00:00")).timestamp())
                issued_epoch = int(issued_at)
                if abs(issued_epoch - block_epoch) > timestamp_tolerance_seconds:
                    contradictions.append("signed receipt issue time is outside configured settlement window")
            except (ValueError, TypeError, OverflowError):
                contradictions.append("invalid settlement or receipt timestamp")
        elif not block_time:
            missing.append("verified block timestamp")
        try:
            if issued_at is not None and authorization.get("valid_from") is not None and int(issued_at) < int(authorization["valid_from"]):
                contradictions.append("resource signer authorization was not yet valid at receipt time")
            if issued_at is not None and authorization.get("valid_until") is not None and int(issued_at) > int(authorization["valid_until"]):
                contradictions.append("resource signer authorization had expired at receipt time")
        except (ValueError, TypeError, OverflowError):
            contradictions.append("invalid receipt or signer-authorization time")

    # Authorization is an external trust input, never inferred from a valid signature.
    if authorization.get("resource_url") is None:
        missing.append("authorization record explicitly scoped to resource URL")
    if not contradictions and not missing and offer_signer and receipt_signer:
        status = "VERIFIED"
        classification = "RESOURCE_ATTRIBUTED"
    else:
        status = "UNRESOLVED"
        classification = "UNRESOLVED"
    result = {
        "status": status,
        "classification": classification,
        "signatures": {
            "offer_valid": offer_signer is not None,
            "receipt_valid": receipt_signer is not None,
            "offer_signer": offer_signer,
            "receipt_signer": receipt_signer,
            "authorization_ref": authorization.get("evidence_ref"),
            "authorization_verification": "EXTERNAL_TRUST_INPUT" if authorization.get("verified") is True else "UNVERIFIED",
            "authorization_evidence_hash": _hash_evidence(auth_document) if isinstance(auth_document, dict) else None,
        },
        "resource": {"id": resource.get("id"), "url": resource_url},
        "settlement": {
            "chain_id": settlement.get("chain_id"),
            "transaction_hash": settlement.get("transaction_hash"),
            "log_index": settlement.get("log_index"),
            "finality": settlement.get("finality"),
            "transfer": settlement.get("transfer"),
        },
        "independent_buyer": "NOT_ESTABLISHED",
        "missing_evidence": sorted(set(missing)),
        "contradictions": sorted(set(contradictions)),
        "evidence_hash": _hash_evidence(evidence),
        "method": "x402-foundation-offer-receipt-eip712-v1+Base-transfer-match",
        "config": {"supported_network": BASE_NETWORK, "supported_asset": BASE_USDC,
                   "finality_states": sorted(FINALITY), "timestamp_tolerance_seconds": timestamp_tolerance_seconds},
    }
    return result


def store_verification(db, evidence: dict[str, Any], result: dict[str, Any]) -> None:
    db.execute(
        """INSERT OR IGNORE INTO payment_attribution_checks
           (evidence_hash, checked_at, resource_id, tx_hash, status, classification, evidence_json, result_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (result["evidence_hash"], datetime.now(timezone.utc).isoformat(),
         (evidence.get("resource") or {}).get("id"),
         (evidence.get("settlement") or {}).get("transaction_hash"),
         result["status"], result["classification"],
         json.dumps(evidence, sort_keys=True, separators=(",", ":")),
         json.dumps(result, sort_keys=True, separators=(",", ":"))),
    )
    db.commit()
