import requests
from nepse import Nepse

class MarketDataService:
    def __init__(self):
        self.nepse = Nepse()
        self.nepse.setTLSVerification(False)
        self.smtm_url = "https://markets.onlinekhabar.com/smtm/search-list/tickers"

    def get_live_prices(self, symbol=None):
        try:
            resp = self.nepse.getPriceVolume()
            if not resp:
                raise ValueError("No data returned")
            return resp
        except Exception:
            if symbol:
                try:
                    return self.nepse.getSymbolMarketDepth(symbol)
                except Exception:
                    return None
            return None

    def get_enriched_data(self):
        try:
            resp = requests.get(self.smtm_url)
            resp.raise_for_status()
            data = resp.json()
            enriched = []
            for item in data.get("response", []):
                ticker = item.get("ticker")
                if ticker:
                    enriched.append({
                        "ticker": ticker,
                        "ticker_name": item.get("ticker_name"),
                        "sector": item.get("sector"),
                        "icon": item.get("icon"),
                        "point_change": item.get("point_change"),
                        "percentage_change": item.get("percentage_change"),
                    })
            return enriched
        except Exception:
            return {}

market_data_service = MarketDataService()
