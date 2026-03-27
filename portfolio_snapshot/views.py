import io

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import openpyxl
from .forms import ImportTransactionsForm
import datetime
from collections import defaultdict
import polars as pl
from .models import Transaction

@login_required
def index(request):
    return render(request, 'portfolio_snapshot/index.html')


@login_required
def import_transactions(request):
    if request.method == 'POST':
        form = ImportTransactionsForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            try:
                wb = openpyxl.load_workbook(filename=io.BytesIO(
                    uploaded_file.read()), data_only=True)
                sheet = wb.active
                rows = list(sheet.iter_rows(min_row=23, values_only=True))

                if not rows:
                    raise ValueError("The file does not contain enough rows.")

                header = rows[0]
                data_rows = rows[1:-1]
                txn_counts = defaultdict(int)
                parsed_txns = []
                for row in data_rows:
                    txn_dict = dict(zip(header, row))
                    txn_no = str(row[1]).strip() if row[1] else None

                    if not txn_no or 'total' in txn_no.lower():
                        continue

                    try:
                        date_str = f"{txn_no[:4]}-{txn_no[4:6]}-{txn_no[6:8]}"
                        stock = str(txn_dict.get('Stock')).upper().strip()
                        txn_data = {
                            'transaction_no': txn_no,
                            'transaction_date': date_str,
                            'stock': stock,
                            'client_name': txn_dict.get('Client Name'),
                            'transaction_type': 'Sell' if 'sell' in str(txn_dict.get('Txn. Type')).lower() else 'Buy',
                            'quantity': int(txn_dict.get('Qty.')),
                            'rate': float(txn_dict.get('Rate')),
                            'amount': int(txn_dict.get('Qty.')) * float(txn_dict.get('Rate')),
                            'nepse_commission': float(txn_dict.get('Nepse Commission')),
                            'sebo_commission': float(txn_dict.get('Sebo Commission')),
                            'broker_commission': float(txn_dict.get('Broker Commission')),
                        }
                        txn_counts[(date_str, stock)] += 1
                        parsed_txns.append(txn_data)

                    except:
                        pass

                # Apply DP Charge Logic (25 / count)
                for txn in parsed_txns:
                    key = (txn['transaction_date'], txn['stock'])
                    count = txn_counts[key]
                    txn['dp_charge'] = round(
                        25.0 / count, 2) if count > 0 else 25.0

                transactions = []
                for p in parsed_txns:
                   
                    txn = Transaction(
                        transaction_no=p['transaction_no'],
                        stock=p['stock'],
                        client_name=p['client_name'],
                        quantity=p['quantity'],
                        rate=p['rate'],
                        amount=p['amount'],
                        transaction_date=p['transaction_date'],
                        transaction_type=p['transaction_type'],
                        nepse_commission=p['nepse_commission'],
                        sebo_commission=p['sebo_commission'],
                        broker_commission=p['broker_commission'],
                        dp_charge=p['dp_charge']
                    )
                    transactions.append(txn)
                    
                Transaction.objects.bulk_create(transactions, ignore_conflicts=True)
                return redirect('portfolio_snapshot:import_transactions')
            except Exception as e:
                print(e)
                form.add_error('file', f"Error processing Excel: {str(e)}")
    else:
        form = ImportTransactionsForm()

    return render(request, 'portfolio_snapshot/import_transactions.html', {'form': form})




@login_required
def sync_corporate_actions(request):
    from .models import CorporateAction
    # Get latest 20 syncs, ordered by last fetch date
    recent_syncs = CorporateAction.objects.order_by('-last_fetch_date')[:20]
    return render(request, 'portfolio_snapshot/sync_corporate_actions.html', {
        'recent_syncs': recent_syncs
    })
