
from django.db import connection
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import polars as pl
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from portfolio_snapshot.models import DailyTransaction
from portfolio_snapshot.utils.portfolio_calculations import portfolio_calculation


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
            commission = row["Broker Commission"] + row["Nepse Commission"]
            total_commsion = commission / 0.994
            regulatory_fee = round(total_commsion, 2) - commission

            trn = DailyTransaction(
                trn_no=str(row["Transaction No."]),
                client_name=row["Client Name"],
                symbol=row["Stock"],
                trn_type=str(row["Txn. Type"]).strip().lower(),
                date=row["Parsed Date"],
                qty=row["Qty."],
                rate=row["Rate"],
                regulatory_fee=regulatory_fee,
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


def portfolio_snapshot_dashboard(request):
    # Read the client_name from the URL query string
    client_name = request.GET.get("client_name")

    if not client_name:
        return JsonResponse({
            "status": "error",
            "message": "Missing 'client_name' in query parameters."
        }, status=400)

    results = portfolio_calculation(
        {
            "client_name": client_name
        }
    )

    return JsonResponse({
        "status": "success",
        "result": results
    })


def nepse_price(request):
    from nepse import Nepse
    nepse = Nepse()
    # This is temporary, until nepse sorts its ssl certificate problem
    nepse.setTLSVerification(False)

    try:
        resp = nepse.getPriceVolume()
    
        return JsonResponse({
            "status": "success",
            "resp": resp,
        }, safe=False)
    except Exception as e:
        return JsonResponse({
            "status": "failed",
            "resp": str(e),
        }, safe=False)
        pass
