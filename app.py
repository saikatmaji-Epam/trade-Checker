import csv
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from trade_checker import evaluate_trades


FOLDER = Path(__file__).parent
TRADES_FILE = FOLDER / "data" / "trades_test.csv"
PORTFOLIOS_FILE = FOLDER / "demo_portfolios.json"


def load_trades():
    with TRADES_FILE.open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def load_portfolios():
    with PORTFOLIOS_FILE.open(encoding="utf-8") as file:
        return json.load(file)


class TradeHandler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self.send_json(
                200,
                {
                    "message": "Trade compliance demo is running.",
                    "open_in_browser": ["/trades", "/portfolios", "/results"],
                    "note": "The portfolio data is for demonstration only.",
                },
            )
        elif self.path == "/trades":
            self.send_json(200, {"trades": load_trades()})
        elif self.path == "/portfolios":
            self.send_json(200, {"portfolios": load_portfolios()})
        elif self.path == "/results":
            results = evaluate_trades(load_trades(), load_portfolios())
            self.send_json(200, {"results": results})
        else:
            self.send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/evaluate":
            self.send_json(404, {"error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            request_data = json.loads(self.rfile.read(length))
            if not isinstance(request_data, dict):
                raise ValueError("Request must be a JSON object")

            trades = request_data.get("trades", load_trades())
            portfolios = request_data.get("portfolios", load_portfolios())
            results = evaluate_trades(trades, portfolios)
        except (json.JSONDecodeError, ValueError, TypeError) as error:
            self.send_json(400, {"error": str(error)})
            return

        self.send_json(200, {"results": results})


if __name__ == "__main__":
    print("Server running: http://127.0.0.1:8000")
    HTTPServer(("127.0.0.1", 8000), TradeHandler).serve_forever()
