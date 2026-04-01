
from django.db import connection
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import polars as pl
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from portfolio_snapshot.models import DailyTransaction


@login_required
def index(request):
    return render(request, 'portfolio_snapshot/index.html')


@login_required
def import_transactions(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed. Use POST.'}, status=405)

    excel_file = request.FILES.get('file')
    if not excel_file:
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    try:
        df = pl.read_excel(
            excel_file.read(),
            engine="calamine",
            read_options={
                "header_row": 22,
            }
        )
        df = df.filter(pl.col("Transaction No.").is_not_null())

        def clean_numeric(col_name):
            return pl.col(col_name).cast(pl.String).str.replace_all(",", "").cast(pl.Float64)

        df = df.with_columns([
            clean_numeric("Broker Commission").fill_null(0.0),
            clean_numeric("Nepse Commission").fill_null(0.0),
            clean_numeric("Sebo Commission").fill_null(0.0),
            clean_numeric("Qty."),
            clean_numeric("Rate"),
        ])

        df = df.with_columns(
            (
                pl.col("Transaction No.").cast(pl.String).str.slice(0, 4) + "-" +
                pl.col("Transaction No.").cast(pl.String).str.slice(4, 2) + "-" +
                pl.col("Transaction No.").cast(pl.String).str.slice(6, 2)
            ).alias("Parsed Date")
        )

        # compute dp charge
        df = df.with_columns(
            pl.len().over(["Parsed Date", "Stock", "Txn. Type",
                           "Client Name"]).alias("txn_count")
        )
        df = df.with_columns(
            (25.0 / pl.col("txn_count")).alias("dp_charge")
        )

        records = df.to_dicts()
        transactions = []

        for row in records:
            trn = DailyTransaction(
                trn_no=str(row["Transaction No."]),
                client_name=row["Client Name"],
                symbol=row["Stock"],
                trn_type=str(row["Txn. Type"]).strip().lower(),
                date=row["Parsed Date"],
                qty=row["Qty."],
                rate=row["Rate"],
                broker_commission=row["Broker Commission"],
                nepse_commission=row["Nepse Commission"],
                sebo_commission=row["Sebo Commission"],
                dp_charge=row["dp_charge"],
            )

            transactions.append(trn)

        DailyTransaction.objects.bulk_create(
            transactions, ignore_conflicts=True)

        return JsonResponse({
            'status': 'success',
            "message": f"Succesfully import {len(records)} data in daily transaction table"

        })

    except pl.exceptions.ComputeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid Excel format or skip_rows mismatch.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def sync_corporate_actions(request):
    from portfolio_snapshot.utils.sync_corporate_action import sync
    from portfolio_snapshot.models import DailyTransaction, CorporateAction, CorporateActionSync
    from django.db.models.functions import Upper

    symbols = list(
        DailyTransaction.objects
        .annotate(upper_symbol=Upper('symbol'))
        .values_list('upper_symbol', flat=True)
        .distinct()
    )

    try:
        corporate_actions = sync(symbols)
        actions_to_create = []
        for item in corporate_actions:
            if not item.get('symbol') or not item.get('book_close_date'):
                continue

            actions_to_create.append(
                CorporateAction(
                    symbol=item['symbol'],
                    corporate_action_type=item['corporate_action_type'],
                    book_close_date=item['book_close_date'],
                    listing_date=item.get('listing_date'),
                    bonus_pct=item.get('bonus_pct', 0.0),
                    cash_dividend_pct=item.get('cash_dividend_pct', 0.0),
                    right_share_pct=item.get('right_share_pct', 0.0),
                )
            )
        CorporateAction.objects.bulk_create(
            actions_to_create,
            ignore_conflicts=True
        )
        CorporateActionSync.objects.create(
            status="Success"
        )
        return JsonResponse({"status": "success", "error": "successfully sync corporate actions"})
    except Exception as e:
        CorporateActionSync.objects.create(
            status="Failed",
            error_log=str(e)
        )
        return JsonResponse({"status": "failed", "error": str(e)}, status=504)


def corporate_action_dashboard(requests):
    from portfolio_snapshot.models import CorporateActionSync, CorporateAction

    sync_history = list(
        CorporateActionSync.objects.values(
            'id',
            'last_fetch_date',
            'status',
            'error_log'
        ).order_by('-last_fetch_date')[:5]
    )

    corporate_actions = list(
        CorporateAction.objects.values(
            "pk",
            "symbol",
            "corporate_action_type",
            "book_close_date",
            "listing_date",
            "bonus_pct",
            "cash_dividend_pct",
            "right_share_pct"
        ).order_by('-book_close_date')
    )

    return JsonResponse({
        "status": "success",
        "sync_history": sync_history,
        "corporate_actions": corporate_actions
    })


def testing(request):
    client_name = "LATA CHAUDHARY (LC456959)"

    # The Raw PostgreSQL Query
    query = """
    WITH client_bounds AS (
        -- Calculate date range for the client once
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

        -- 2. Corporate Actions (All fields included)
        SELECT 
            ca.id, 
            ca.symbol, 
            ca.book_close_date AS event_date, 
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

    with connection.cursor() as cursor:
        # We pass client_name twice: once for the CTE and once for the Transaction filter
        cursor.execute(query, [client_name, client_name])

        # Helper to map column names to row values
        columns = [col[0] for col in cursor.description]
        results = [
            dict(zip(columns, row)) 
            for row in cursor.fetchall()
        ]

    return JsonResponse({
        "status": "success",
        "result": results
    })