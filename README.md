# Trade Checker

A simple Python demo that checks whether trades are valid for a portfolio. It looks at cash, restricted securities, holdings, selling limits, and position concentration.

## Run it

```powershell
python app.py
```

Open http://127.0.0.1:8000

## Useful links

- `/trades` - sample trades
- `/portfolios` - sample portfolios
- `/results` - evaluated trade results

## Try an evaluation

Send a POST request to `/evaluate` with JSON containing `trades` and `portfolios`. The API returns an approved, rejected, or manual-sign-off result for each trade.
