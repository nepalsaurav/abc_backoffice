from collections import deque
import json
from django.db import connection

from decimal import Decimal

BASE_PRICE = {"SHL": Decimal('10')}
DEFAULT_BASE_PRICE = Decimal('100')


def combine_query(client_name: str):
    query = """
    WITH client_bounds AS (
        SELECT MIN(date) as start_date, MAX(date) as end_date
        FROM daily_transactions
        WHERE client_name = %s
    )
    (
        -- 1. Transactions
        SELECT 
            id, 
            symbol, 
            date AS event_date, 
            'Transaction' AS source, 
            'daily_transactions' AS collection_name, 
            jsonb_build_object(
                'trn_no', trn_no, 
                'client_name', client_name,
                'trn_type', trn_type,
                'qty', qty, 
                'rate', rate,
                'broker_commission', broker_commission,
                'nepse_commission', nepse_commission,
                'sebo_commission', sebo_commission,
                'dp_charge', dp_charge,
                'regulatory_fee', regulatory_fee
            ) AS metadata
        FROM daily_transactions 
        WHERE client_name = %s

        UNION ALL

        -- 2. Corporate Actions (Phase 1: Book Close / Provisional)
        SELECT 
            ca.id, 
            ca.symbol, 
            ca.book_close_date AS event_date, 
            'corporate_action' AS source, 
            'corporate_actions' AS collection_name, 
            jsonb_build_object(
                'corporate_action_type', ca.corporate_action_type,
                'action_stage', 'book_close',
                'bonus_pct', ca.bonus_pct, 
                'cash_dividend_pct', ca.cash_dividend_pct,
                'right_share_pct', ca.right_share_pct
            ) AS metadata
        FROM corporate_actions ca, client_bounds cb
        WHERE ca.book_close_date BETWEEN cb.start_date AND cb.end_date

        UNION ALL

        -- 3. Corporate Actions (Phase 2: Listing / Tradable)
        SELECT 
            ca.id, 
            ca.symbol, 
            ca.listing_date AS event_date, 
            'corporate_action' AS source, 
            'corporate_actions' AS collection_name, 
            jsonb_build_object(
                'corporate_action_type', ca.corporate_action_type,
                'action_stage', 'listing',
                'bonus_pct', ca.bonus_pct, 
                'cash_dividend_pct', ca.cash_dividend_pct,
                'right_share_pct', ca.right_share_pct
            ) AS metadata
        FROM corporate_actions ca, client_bounds cb
        WHERE ca.listing_date IS NOT NULL 
          AND ca.book_close_date BETWEEN cb.start_date AND cb.end_date
    )
    ORDER BY event_date ASC;
    """

    results = []
    with connection.cursor() as cursor:
        cursor.execute(query, [client_name, client_name])
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return results


def get_current_wacc(wacc_state, symbol):
    if symbol in wacc_state and wacc_state[symbol]["qty"] > 0:
        return wacc_state[symbol]["cost"] / wacc_state[symbol]["qty"]
    return BASE_PRICE.get(symbol, DEFAULT_BASE_PRICE)


def handle_buy_transactions(
    row, meta, holdings, wacc_state, symbol, current_balance, client_ledger
):
    qty = meta.get("qty")
    rate = meta.get("rate")
    gross_amount = qty * rate

    total_fees = (
        meta.get("sebo_commission", 0)
        + meta.get("nepse_commission", 0)
        + meta.get("broker_commission", 0)
        + meta.get("regulatory_fee", 0)
        + meta.get("dp_charge", 0)
    )

    net_amount = gross_amount + total_fees

    current_balance[symbol] += qty

    holdings[symbol].append(
        {
            "date": row.get("event_date"),
            "qty": qty,
            "rate": rate,
            "type": "buy",
            "is_provisional": False,
        }
    )

    wacc_state[symbol]["qty"] += qty
    wacc_state[symbol]["cost"] += net_amount

    client_ledger.append(
        {
            "date": row.get("event_date"),
            "symbol": symbol,
            "trn_no": meta.get("trn_no", "N/A"),
            "transaction_type": "Buy",
            "in_qty": qty,
            "out_qty": 0,
            "rate": rate,
            "gross_amount": round(gross_amount, 4),
            "net_amount": round(net_amount, 4),
            "fees": {
                "broker": meta.get("broker_commission", 0),
                "sebo": meta.get("sebo_commission", 0),
                "nepse": meta.get("nepse_commission", 0),
                "dp_charge": meta.get("dp_charge", 0),
                "regulatory": meta.get("regulatory_fee", 0),
            },
            "capital_gain": 0,
            "cgt_total": 0,
            "cgt_5_pct": 0,
            "cgt_7_5_pct": 0,
            "wacc": round(get_current_wacc(wacc_state, symbol), 4),
            "balance_qty": current_balance[symbol],
        }
    )


def handle_sell_transactions(
    row, meta, holdings, wacc_state, symbol, current_balance, client_ledger, excess_sells
):
    sell_qty = meta.get("qty")
    sell_date = row.get("event_date")
    sell_rate = meta.get("rate")
    gross_amount = sell_qty * sell_rate

    current_wacc = get_current_wacc(wacc_state, symbol)
    current_balance[symbol] -= sell_qty

    total_fees = (
        meta.get("sebo_commission", 0)
        + meta.get("nepse_commission", 0)
        + meta.get("broker_commission", 0)
        + meta.get("dp_charge", 0)
        + meta.get("regulatory_fee", 0)
    )

    net_amount = gross_amount - total_fees
    total_cost_of_sold_units = sell_qty * current_wacc
    capital_gain = net_amount - total_cost_of_sold_units

    units_to_process = sell_qty
    cgt_5_pct = 0
    cgt_7_5_pct = 0
    provisional_buffer = []

    while units_to_process > 0 and symbol in holdings and holdings[symbol]:
        oldest = holdings[symbol].popleft()

        if oldest.get("is_provisional", False):
            provisional_buffer.append(oldest)
            continue

        days_held = (sell_date - oldest["date"]).days
        is_long_term = days_held > 365
        tax_rate = Decimal('0.05') if is_long_term else Decimal('0.075')

        take_qty = min(oldest["qty"], units_to_process)

        if capital_gain > 0:
            chunk_profit = (take_qty / sell_qty) * capital_gain
            if is_long_term:
                cgt_5_pct += chunk_profit * tax_rate
            else:
                cgt_7_5_pct += chunk_profit * tax_rate

        units_to_process -= take_qty

        if oldest["qty"] > take_qty:
            oldest["qty"] -= take_qty
            holdings[symbol].appendleft(oldest)
            break

    for batch in reversed(provisional_buffer):
        holdings[symbol].appendleft(batch)

    if units_to_process > 0:
        if capital_gain > 0:
            fallback_profit = (units_to_process / sell_qty) * capital_gain
            cgt_7_5_pct += fallback_profit * Decimal('0.075')
        
        excess_qty = units_to_process
        if symbol not in excess_sells:
            excess_sells[symbol] = {"qty": Decimal('0'), "value": Decimal('0.0')}
        excess_sells[symbol]["qty"] += excess_qty
        excess_sells[symbol]["value"] += (excess_qty / sell_qty) * net_amount
    else:
        excess_qty = 0

    qty_from_brokerage = sell_qty - excess_qty
    wacc_state[symbol]["qty"] -= qty_from_brokerage

    if wacc_state[symbol]["qty"] <= 0:
        wacc_state[symbol]["qty"] = Decimal('0')
        wacc_state[symbol]["cost"] = Decimal('0.0')
    else:
        wacc_state[symbol]["cost"] = wacc_state[symbol]["qty"] * current_wacc

    total_cgt = cgt_5_pct + cgt_7_5_pct

    client_ledger.append(
        {
            "date": sell_date,
            "symbol": symbol,
            "trn_no": meta.get("trn_no", "N/A"),
            "transaction_type": "Sell",
            "in_qty": 0,
            "out_qty": sell_qty,
            "rate": sell_rate,
            "gross_amount": round(gross_amount, 4),
            "net_amount": round(net_amount, 4),
            "fees": {
                "broker": meta.get("broker_commission", 0),
                "sebo": meta.get("sebo_commission", 0),
                "nepse": meta.get("nepse_commission", 0),
                "dp_charge": meta.get("dp_charge", 0),
                "regulatory": meta.get("regulatory_fee", 0),
            },
            "capital_gain": round(capital_gain, 4),
            "cgt_total": round(total_cgt, 4),
            "cgt_5_pct": round(cgt_5_pct, 4),
            "cgt_7_5_pct": round(cgt_7_5_pct, 4),
            "wacc": round(current_wacc, 4),
            "balance_qty": current_balance[symbol],
        }
    )


def handle_corporate_actions(
    row, meta, holdings, wacc_state, symbol, current_balance, client_ledger
):
    action_stage = meta.get("action_stage")
    action_type = meta.get("corporate_action_type")
    event_date = row.get("event_date")
    ca_id = row.get("id")
    base_price = BASE_PRICE.get(symbol, DEFAULT_BASE_PRICE)

    # --- PHASE 1: BOOK CLOSE (Calculate shares, mark as provisional) ---
    if action_stage == "book_close":
        # Calculate holdings at this point (excluding any pending provisionals)
        total_held = sum(batch["qty"] for batch in holdings[symbol] if not batch.get("is_provisional", False))
        
        if total_held <= 0:
            return

        if action_type == "bonus":
            bonus_pct = meta.get("bonus_pct", 0)
            bonus_qty = int(total_held * (bonus_pct / 100))
            if bonus_qty > 0:
                current_balance[symbol] += bonus_qty
                cost = bonus_qty * base_price

                # Append as provisional. WACC is NOT updated yet.
                holdings[symbol].append({
                    "date": event_date,
                    "qty": bonus_qty,
                    "rate": base_price,
                    "type": "bonus",
                    "is_provisional": True,
                    "ca_id": ca_id,
                    "cost": cost
                })

                client_ledger.append({
                    "date": event_date,
                    "symbol": symbol,
                    "trn_no": "CORP_ACTION",
                    "transaction_type": "Bonus Share (Provisional)",
                    "in_qty": bonus_qty,
                    "out_qty": 0,
                    "rate": base_price,
                    "gross_amount": 0,
                    "net_amount": 0,
                    "fees": {},
                    "capital_gain": 0,
                    "cgt_total": 0,
                    "cgt_5_pct": 0,
                    "cgt_7_5_pct": 0,
                    "wacc": round(get_current_wacc(wacc_state, symbol), 4),
                    "balance_qty": current_balance[symbol],
                    "remarks": f"{bonus_pct}% Bonus Declared",
                })

        elif action_type == "right_share":
            right_pct = meta.get("right_share_pct", 0)
            right_qty = int(total_held * (right_pct / 100))
            if right_qty > 0:
                current_balance[symbol] += right_qty
                cost = right_qty * base_price

                holdings[symbol].append({
                    "date": event_date,
                    "qty": right_qty,
                    "rate": base_price,
                    "type": "right_share",
                    "is_provisional": True,
                    "ca_id": ca_id,
                    "cost": cost
                })

                client_ledger.append({
                    "date": event_date,
                    "symbol": symbol,
                    "trn_no": "CORP_ACTION",
                    "transaction_type": "Right Share (Provisional)",
                    "in_qty": right_qty,
                    "out_qty": 0,
                    "rate": base_price,
                    "gross_amount": cost,
                    "net_amount": cost,
                    "fees": {},
                    "capital_gain": 0,
                    "cgt_total": 0,
                    "cgt_5_pct": 0,
                    "cgt_7_5_pct": 0,
                    "wacc": round(get_current_wacc(wacc_state, symbol), 4),
                    "balance_qty": current_balance[symbol],
                    "remarks": f"{right_pct}% Right Share Issued",
                })

        elif action_type == "cash_dividend":
            div_pct = meta.get("cash_dividend_pct", 0)
            gross_dividend = total_held * base_price * (div_pct / 100)
            
            if gross_dividend > 0:
                client_ledger.append({
                    "date": event_date,
                    "symbol": symbol,
                    "trn_no": "CORP_ACTION",
                    "transaction_type": "Cash Dividend",
                    "in_qty": Decimal('0'),
                    "out_qty": Decimal('0'),
                    "rate": Decimal('0'),
                    "gross_amount": round(gross_dividend, 4),
                    "net_amount": round(gross_dividend * Decimal('0.95'), 4),
                    "fees": {},
                    "capital_gain": Decimal('0'),
                    "cgt_total": round(gross_dividend * Decimal('0.05'), 4),
                    "cgt_5_pct": Decimal('0'),
                    "cgt_7_5_pct": Decimal('0'),
                    "wacc": round(get_current_wacc(wacc_state, symbol), 4),
                    "balance_qty": current_balance[symbol],
                    "remarks": f"{div_pct}% Cash Dividend",
                })

    # --- PHASE 2: LISTING (Transfer provisional to tradable) ---
    elif action_stage == "listing":
        listed_qty = 0
        total_cost = 0
        
        # Locate the specific provisional shares by ca_id
        for batch in holdings[symbol]:
            if batch.get("ca_id") == ca_id and batch.get("is_provisional"):
                batch["is_provisional"] = False  # Mark as tradable
                listed_qty += batch["qty"]
                total_cost += batch.get("cost", batch["qty"] * batch["rate"])
                
        if listed_qty > 0:
            # Now we update the WACC state since the shares are listed
            wacc_state[symbol]["qty"] += listed_qty
            wacc_state[symbol]["cost"] += total_cost
            
            txn_type = "Bonus Share (Listed)" if action_type == "bonus" else "Right Share (Listed)"
            
            client_ledger.append({
                "date": event_date,
                "symbol": symbol,
                "trn_no": "CORP_ACTION",
                "transaction_type": txn_type,
                "in_qty": 0, # Qty is already recorded in balance during Book Close
                "out_qty": 0,
                "rate": base_price,
                "gross_amount": 0,
                "net_amount": 0,
                "fees": {},
                "capital_gain": 0,
                "cgt_total": 0,
                "cgt_5_pct": 0,
                "cgt_7_5_pct": 0,
                "wacc": round(get_current_wacc(wacc_state, symbol), 4),
                "balance_qty": current_balance[symbol],
                "remarks": f"{listed_qty} shares transferred to tradable",
            })


def portfolio_calculation(ctx: dict):
    query_results = combine_query(client_name=ctx["client_name"])

    holdings = {}
    current_balance = {}
    client_ledger = []
    wacc_state = {}
    excess_sells = {}

    for row in query_results:
        source = row.get("source")
        symbol = row.get("symbol")
        meta = json.loads(row.get("metadata"), parse_float=Decimal)

        if symbol not in holdings:
            holdings[symbol] = deque()
            current_balance[symbol] = Decimal('0')
            wacc_state[symbol] = {"qty": Decimal('0'), "cost": Decimal('0.0')}

        if source == "Transaction":
            trn_type = meta.get("trn_type")
            if trn_type == "buy":
                handle_buy_transactions(
                    row, meta, holdings, wacc_state, symbol, current_balance, client_ledger
                )
            elif trn_type == "sell":
                handle_sell_transactions(
                    row, meta, holdings, wacc_state, symbol, current_balance, client_ledger, excess_sells
                )

        elif source == "corporate_action":
            # The action_type is now fetched directly inside the handler from meta
            handle_corporate_actions(
                row, meta, holdings, wacc_state, symbol, current_balance, client_ledger
            )

    # --- Formatting final balance output ---
    formatted_balance = []
    for symbol, total_qty in current_balance.items():
        if total_qty > 0:
            # Calculate provisional quantity from the current holdings queue
            provisional_qty = sum(
                batch["qty"] for batch in holdings[symbol] if batch.get("is_provisional")
            )

            formatted_balance.append({
                "symbol": symbol,
                "qty": total_qty,
                "wacc": round(get_current_wacc(wacc_state, symbol), 4),
                "total_investment_amount": round(wacc_state[symbol]["cost"], 4),
                "provisional_qty": provisional_qty
            })

    formatted_excess = []
    for sym, data in excess_sells.items():
        formatted_excess.append({
            "symbol": sym,
            "qty": data["qty"],
            "total_sales_value": round(data["value"], 4)
        })

    return {
        "current_balance": formatted_balance,
        "client_ledger": client_ledger,
        "excess_sells": formatted_excess
    }