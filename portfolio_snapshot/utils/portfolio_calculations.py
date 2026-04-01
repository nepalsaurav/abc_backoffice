from collections import deque
import json
from django.db import connection

BASE_PRICE = {
    "SHL": 10
}
DEFAULT_BASE_PRICE = 100

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
                'dp_charge', dp_charge
            ) AS metadata
        FROM daily_transactions 
        WHERE client_name = %s

        UNION ALL

        -- 2. Corporate Actions
        SELECT 
            ca.id, 
            ca.symbol, 
            COALESCE(ca.listing_date, ca.book_close_date) AS event_date, 
            ca.corporate_action_type AS source, 
            'corporate_actions' AS collection_name, 
            jsonb_build_object(
                'corporate_action_type', ca.corporate_action_type,
                'listing_date', ca.listing_date,
                'bonus_pct', ca.bonus_pct, 
                'cash_dividend_pct', ca.cash_dividend_pct,
                'right_share_pct', ca.right_share_pct
            ) AS metadata
        FROM corporate_actions ca, client_bounds cb
        WHERE ca.book_close_date BETWEEN cb.start_date AND cb.end_date
    )
    ORDER BY event_date ASC;
    """

    results = []
    with connection.cursor() as cursor:
        cursor.execute(query, [client_name, client_name])
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return results


def get_current_wacc(holdings, symbol):
    """Helper to calculate WACC at any given moment for the ledger"""
    sellable_batches = [b for b in holdings[symbol] if not b.get("is_provisional", False)]
    total_qty = sum(batch["qty"] for batch in sellable_batches)
    if total_qty > 0:
        total_cost = sum(batch["cost_of_buying"] for batch in sellable_batches)
        return total_cost / total_qty
    return BASE_PRICE.get(symbol, DEFAULT_BASE_PRICE)


def handle_buy_transactions(row, meta, holdings, symbol, current_balance, client_ledger):
    qty = meta.get("qty")
    rate = meta.get("rate")
    
    current_balance[symbol] += qty

    cost_of_buying = (qty * rate +
                      meta.get("sebo_commission", 0) +
                      meta.get("nepse_commission", 0) +
                      meta.get("broker_commission", 0) +
                      meta.get("dp_charge", 0))
                      
    holdings[symbol].append({
        "date": row.get("event_date"),
        "qty": qty,
        "rate": rate,
        "cost_of_buying": round(cost_of_buying, 4),
        "average_cost": round((cost_of_buying / qty), 4),
        "type": "buy",
        "is_provisional": False
    })

    client_ledger.append({
        "date": row.get("event_date"),
        "symbol": symbol,
        "transaction_type": "Buy",
        "in_qty": qty,
        "out_qty": 0,
        "rate": rate,
        "amount": round(cost_of_buying, 4),
        "wacc": round(get_current_wacc(holdings, symbol), 4),
        "balance_qty": current_balance[symbol]
    })


def handle_sell_transactions(row, meta, holdings, symbol, current_balance, client_ledger):
    sell_qty = meta.get("qty")
    sell_date = row.get("event_date")
    sell_rate = meta.get("rate")
    
    current_wacc = get_current_wacc(holdings, symbol)
    current_balance[symbol] -= sell_qty
    
    units_to_process = sell_qty
    total_cost_of_sold_units = 0
    total_cgt = 0
    
    net_revenue = (sell_qty * sell_rate) - (
        meta.get("sebo_commission", 0) + meta.get("nepse_commission", 0) +
        meta.get("broker_commission", 0) + meta.get("dp_charge", 0)
    )

    provisional_buffer = []

    while units_to_process > 0 and symbol in holdings and holdings[symbol]:
        oldest = holdings[symbol].popleft()

        if oldest.get("is_provisional", False):
            provisional_buffer.append(oldest)
            continue

        days_held = (sell_date - oldest["date"]).days
        tax_rate = 0.05 if days_held > 365 else 0.075

        take_qty = min(oldest["qty"], units_to_process)
        fractional_cost = (take_qty / oldest["qty"]) * oldest["cost_of_buying"]
        
        proportional_revenue = (take_qty / sell_qty) * net_revenue
        chunk_profit = proportional_revenue - fractional_cost

        if chunk_profit > 0:
            total_cgt += chunk_profit * tax_rate

        total_cost_of_sold_units += fractional_cost
        units_to_process -= take_qty

        if oldest["qty"] > take_qty:
            oldest["qty"] -= take_qty
            oldest["cost_of_buying"] -= fractional_cost
            holdings[symbol].appendleft(oldest)
            break 

    for batch in reversed(provisional_buffer):
        holdings[symbol].appendleft(batch)

    if units_to_process > 0:
        fallback_cost = units_to_process * current_wacc
        total_cost_of_sold_units += fallback_cost
        fallback_revenue = (units_to_process / sell_qty) * net_revenue
        fallback_profit = fallback_revenue - fallback_cost
        
        if fallback_profit > 0:
            total_cgt += fallback_profit * 0.075 
        
        units_to_process = 0

    capital_gain = net_revenue - total_cost_of_sold_units

    client_ledger.append({
        "date": sell_date,
        "symbol": symbol,
        "transaction_type": "Sell",
        "in_qty": 0,
        "out_qty": sell_qty,
        "rate": sell_rate,
        "amount": round(net_revenue, 4), 
        "capital_gain": round(capital_gain, 4),
        "cgt": round(total_cgt, 4),
        "wacc": round(current_wacc, 4),
        "balance_qty": current_balance[symbol]
    })


def handle_corporate_actions(row, meta, holdings, symbol, current_balance, client_ledger, action_type):
    total_held = sum(batch["qty"] for batch in holdings[symbol])
    if total_held <= 0:
        return # Client held no shares at book closure

    event_date = row.get("event_date")
    base_price = BASE_PRICE.get(symbol, DEFAULT_BASE_PRICE)
    is_provisional = False if meta.get("listing_date") else True

    if action_type == "bonus":
        bonus_qty = int(total_held * (meta.get("bonus_pct", 0) / 100))
        if bonus_qty > 0:
            current_balance[symbol] += bonus_qty
            cost = bonus_qty * base_price
            
            holdings[symbol].append({
                "date": event_date, "qty": bonus_qty, "rate": base_price,
                "cost_of_buying": cost, "average_cost": base_price,
                "type": "bonus", "is_provisional": is_provisional
            })
            
            client_ledger.append({
                "date": event_date, "symbol": symbol, "transaction_type": "Bonus Share",
                "in_qty": bonus_qty, "out_qty": 0, "rate": base_price,
                "amount": 0, "capital_gain": 0, "cgt": 0,
                "wacc": round(get_current_wacc(holdings, symbol), 4),
                "balance_qty": current_balance[symbol]
            })

    elif action_type == "right_share":
        right_qty = int(total_held * (meta.get("right_share_pct", 0) / 100))
        if right_qty > 0:
            current_balance[symbol] += right_qty
            cost = right_qty * base_price 
            
            holdings[symbol].append({
                "date": event_date, "qty": right_qty, "rate": base_price,
                "cost_of_buying": cost, "average_cost": base_price,
                "type": "right_share", "is_provisional": is_provisional
            })
            
            client_ledger.append({
                "date": event_date, "symbol": symbol, "transaction_type": "Right Share",
                "in_qty": right_qty, "out_qty": 0, "rate": base_price,
                "amount": cost, 
                "capital_gain": 0, "cgt": 0,
                "wacc": round(get_current_wacc(holdings, symbol), 4),
                "balance_qty": current_balance[symbol]
            })

    elif action_type == "cash_dividend":
        # cash dividends are calculated on the paid-up value (base_price)
        gross_dividend = total_held * base_price * (meta.get("cash_dividend_pct", 0) / 100)
            
        client_ledger.append({
            "date": event_date, "symbol": symbol, "transaction_type": "Cash Dividend",
            "in_qty": 0, "out_qty": 0, "rate": 0,
            "amount": round(gross_dividend, 4),
            "capital_gain": 0, "cgt": 0,
            "wacc": round(get_current_wacc(holdings, symbol), 4),
            "balance_qty": current_balance[symbol]
        })


def portfolio_calculation(ctx: dict):
    query_results = combine_query(client_name=ctx["client_name"])

    holdings = {}
    current_balance = {}
    client_ledger = [] 

    for row in query_results:
        source = row.get("source")
        symbol = row.get("symbol")
        meta = json.loads(row.get("metadata"))

        if symbol not in holdings:
            holdings[symbol] = deque()
            current_balance[symbol] = 0

        if source == "Transaction":
            trn_type = meta.get("trn_type")
            if trn_type == "buy":
                handle_buy_transactions(row, meta, holdings, symbol, current_balance, client_ledger)
            elif trn_type == "sell":
                handle_sell_transactions(row, meta, holdings, symbol, current_balance, client_ledger)

        # Catch all corporate actions (bonus, right_share, cash_dividend)
        elif source in ["bonus", "right", "cash_dividend"]:
            handle_corporate_actions(row, meta, holdings, symbol, current_balance, client_ledger, action_type=source)

    portfolio = {symbol: list(queue) for symbol, queue in holdings.items()}

    return {
        "current_balance": current_balance,
        "client_ledger": client_ledger,  
        "portfolio_history": portfolio
    }