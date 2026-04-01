import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def clean_date(date_str):
    if not date_str or not isinstance(date_str, str):
        return None
    date_str = date_str.strip().split(' ')[0]
    if date_str in ["", "-", "—", "None", "null"]:
        return None
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except ValueError:
        return None

def get_dividend_history(ctx: dict):
    url = "https://www.sharesansar.com/company-dividend"
    headers = {
        "x-csrf-token": ctx['csrf_token'],
        "x-requested-with": "XMLHttpRequest",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    }
    payload = {
        "draw": "1",
        "start": "0",
        "length": "50",
        "search[value]": "",
        "search[regex]": "false",
        "company": ctx['company_id'],
    }

    try:
        response = ctx['session'].post(url, headers=headers, data=payload)
        raw_data = response.json()
        
        for item in raw_data.get('data', []):
            clean_bc_date = clean_date(item.get('bookclose_date'))
            clean_listing_date = clean_date(item.get('bonus_listing_date'))
            
            bonus_pct = float(item.get('bonus_share', 0) or 0)
            cash_dividend_pct = float(item.get('cash_dividend', 0) or 0)

            if bonus_pct > 0:
                ctx['formatted_list'].append({
                    "symbol": ctx['symbol'],
                    "corporate_action_type": "bonus",
                    'book_close_date': clean_bc_date,
                    'bonus_pct': bonus_pct,
                    'listing_date': clean_listing_date,
                })
            if cash_dividend_pct > 0:
                 ctx['formatted_list'].append({
                    "symbol": ctx['symbol'],
                    "corporate_action_type": "cash_dividend",
                    'book_close_date': clean_bc_date,
                    'cash_dividend_pct': cash_dividend_pct,
                    'listing_date': clean_listing_date,
                })        
    except Exception as e:
        print(f"Error fetching data for {ctx['symbol']}: {e}")

def get_right_share_history(ctx: dict):
    url = "https://www.sharesansar.com/company-rightshare"
    headers = {
        "x-csrf-token": ctx['csrf_token'],
        "x-requested-with": "XMLHttpRequest",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    }
    payload = {
        "draw": "1",
        "start": "0",
        "length": "50",
        "search[value]": "",
        "search[regex]": "false",
        "company": ctx['company_id'],
    }

    try:
        response = ctx['session'].post(url, headers=headers, data=payload)
        raw_data = response.json()
        
        for item in raw_data.get('data', []):
            clean_bc_date = clean_date(item.get('final_date'))
            clean_listing_date = clean_date(item.get('listing_date'))
            
            ratio = item.get('ratio_value')
            if ratio and ":" in ratio:
                first, second = ratio.split(":")[0], ratio.split(":")[1]
                right_share_pct = (float(second) / float(first)) * 100
                
                ctx['formatted_list'].append({
                        "symbol": ctx['symbol'],
                        "corporate_action_type": "right",
                        'book_close_date': clean_bc_date,
                        'right_share_pct': right_share_pct,
                        'listing_date': clean_listing_date,
                    })   
    except Exception as e:
        print(f"Error fetching Right Share data for {ctx['symbol']}: {e}")

def sync(symbols):
    session = requests.Session()
    resp = session.get("https://www.sharesansar.com")
    soup = BeautifulSoup(resp.content, 'html.parser')
    
    meta_tag = soup.find('meta', attrs={'name': '_token'})
    if not meta_tag:
        raise Exception("CSRF token meta tag not found")

    token = meta_tag.get("content")
    script_tag = soup.find('script', string=re.compile('var cmpjson'))

    companies = []
    if script_tag:
        match = re.search(r'var cmpjson\s*=\s*(\[.*?\]);', script_tag.string, re.DOTALL)
        if match:
            companies = json.loads(match.group(1))
    
    formatted_results = []
    
    for symbol in symbols:
        company_info = next((c for c in companies if c['symbol'] == symbol), None)
        if company_info:
            context = {
                "session": session,
                "symbol": symbol,
                "company_id": company_info["id"],
                "csrf_token": token,
                "formatted_list": formatted_results
            }
            try:
                get_dividend_history(context)
                get_right_share_history(context)
            except:
                pass
        
    return formatted_results