"""
The MCP server: wraps Razorpay actions as MCP tools. This is a real
MCPServer instance (mcp==2.x SDK) - the agent talks to it over the actual
MCP protocol (in-process transport for the main demo; see agent.py's
comment on swapping to a stdio subprocess for a "real" deployment).

Deliberately thin: no policy logic lives here. By the time a call reaches
this file, the gate has already approved it. This server's only job is to
execute exactly what it's told and report back honestly.

Money-moving tools (create_payment_link, create_retry_order) route through
Razorpay's OWN OFFICIAL MCP server (razorpay_mcp_client.py -> the real
razorpay/razorpay-mcp-server, not a shim) whenever real rzp_test_ keys are
set. With no keys set, they fall back to razorpay_client.py's in-process
simulate mode - the official server has no simulate mode of its own, so
this is the only way the pipeline runs before you've created a Razorpay
account.
"""

import json
import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from razorpay_client import RazorpayClient, SIMULATE
from razorpay_mcp_client import call_official_tool

DATA_PATH = Path(__file__).parent.parent / "data" / "halted_subscriptions.json"

# Route stretch goal: requires a real onboarded Linked Account, which is a
# manual Razorpay dashboard step outside this codebase's control. Defaults
# to a labeled fake ID (forces simulate mode for this tool specifically)
# unless a real one is provided.
PARTNER_LINKED_ACCOUNT_ID = os.getenv("RAZORPAY_PARTNER_LINKED_ACCOUNT_ID", "acc_sim_partner001")

server = MCPServer(name="razorpay-recovery-agent")
_rp = RazorpayClient()


@server.tool()
def list_halted_subscriptions() -> list[dict]:
    """Return all synthetic halted-subscription records to evaluate."""
    if not DATA_PATH.exists():
        return []
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


@server.tool()
async def create_payment_link(subscription_id: str, amount_paise: int, description: str) -> dict:
    """Create a Razorpay payment link to nudge a customer to fix payment."""
    if SIMULATE:
        return _rp.create_payment_link(amount_paise, description, subscription_id)
    result = await call_official_tool("create_payment_link", {
        "amount": amount_paise,
        "currency": "INR",
        "description": description,
        "notes": {"subscription_id": subscription_id, "source": "recovery-agent"},
    })
    result["simulated"] = False
    result["via_official_razorpay_mcp_server"] = True
    return result


@server.tool()
async def create_retry_order(subscription_id: str, amount_paise: int) -> dict:
    """Create a Razorpay order representing a retry attempt."""
    if SIMULATE:
        return _rp.create_retry_order(amount_paise, subscription_id)
    result = await call_official_tool("create_order", {
        "amount": amount_paise,
        "currency": "INR",
        "notes": {"subscription_id": subscription_id, "source": "recovery-agent"},
    })
    result["simulated"] = False
    result["via_official_razorpay_mcp_server"] = True
    return result


@server.tool()
def initiate_route_transfer(subscription_id: str, amount_paise: int, partner_share_paise: int) -> dict:
    """
    Stretch goal: split a recovered payment between the merchant and a
    second party (e.g. a referral partner) via Razorpay Route, instead of
    a single-party checkout. Not available on the official MCP server (it
    has no Route/transfer tools as of this build - checked directly against
    its tool list) so this goes through razorpay_client.py's own Route
    wrapper instead.
    """
    return _rp.create_route_split_order(
        amount_paise, subscription_id, PARTNER_LINKED_ACCOUNT_ID, partner_share_paise
    )


@server.tool()
def flag_for_manual_review(subscription_id: str, reason: str) -> dict:
    """Record that a subscription needs a human, not automated action (fraud/unrecoverable)."""
    return {"subscription_id": subscription_id, "flagged": True, "reason": reason}


if __name__ == "__main__":
    server.run(transport="stdio")
