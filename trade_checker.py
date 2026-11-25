from decimal import Decimal, InvalidOperation


def to_decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("A number is required")


def rejected(reason):
    return {"decision": "Rejected", "reason": reason}


def evaluate_trade(trade, portfolios):
    if not isinstance(trade, dict):
        return rejected("Invalid trade data.")

    try:
        quantity = to_decimal(trade["quantity"])
        price = to_decimal(trade["price"])
        action = trade["action"]
        portfolio_id = trade["portfolio_id"]
        security_id = trade["security_id"]
    except (KeyError, TypeError, ValueError):
        return rejected("Invalid trade data.")

    if (
        not quantity.is_finite()
        or not price.is_finite()
        or quantity <= 0
        or price <= 0
        or action not in ("Buy", "Sell")
        or not isinstance(portfolio_id, str)
        or not isinstance(security_id, str)
        or not portfolio_id
        or not security_id
    ):
        return rejected("Invalid trade data.")

    if portfolio_id not in portfolios:
        raise ValueError("Unknown portfolio: " + portfolio_id)

    portfolio = portfolios[portfolio_id]
    try:
        cash = to_decimal(portfolio["cash_balance"])
        limit = to_decimal(portfolio["max_position_pct"])
        restricted = portfolio["restricted_securities"]
        holdings = portfolio["current_holdings"]
        if (
            not cash.is_finite()
            or not limit.is_finite()
            or cash < 0
            or limit < 0
            or limit > 1
            or not isinstance(restricted, list)
            or not isinstance(holdings, list)
        ):
            raise ValueError("Invalid portfolio data")

        parsed_holdings = []
        for holding in holdings:
            held_id = holding["security_id"]
            held_quantity = to_decimal(holding["quantity"])
            market_price = to_decimal(holding["market_price"])
            if (
                not isinstance(held_id, str)
                or not held_quantity.is_finite()
                or not market_price.is_finite()
                or held_quantity < 0
                or market_price <= 0
            ):
                raise ValueError("Invalid holding data")
            parsed_holdings.append((held_id, held_quantity, market_price))
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Invalid portfolio data") from error

    if security_id in restricted:
        return rejected("Security is restricted for this portfolio.")

    owned_quantity = sum(
        (qty for held_id, qty, _ in parsed_holdings if held_id == security_id),
        Decimal("0"),
    )

    if action == "Sell":
        if owned_quantity < quantity:
            return rejected("Insufficient holdings to sell.")
        return {"decision": "Approved", "reason": "Trade passed all checks."}

    cost = quantity * price
    if cost > cash:
        return rejected("Insufficient cash for this buy order.")

    cash_after = cash - cost
    position_value = (owned_quantity + quantity) * price
    other_value = sum(
        (
            qty * market_price
            for held_id, qty, market_price in parsed_holdings
            if held_id != security_id
        ),
        Decimal("0"),
    )
    portfolio_value = cash_after + position_value + other_value

    if position_value > limit * portfolio_value:
        return {
            "decision": "Needs Manual Sign-off",
            "reason": "Exceeds maximum position concentration — requires approval.",
        }

    return {"decision": "Approved", "reason": "Trade passed all checks."}


def evaluate_trades(trades, portfolios):
    if not isinstance(trades, list) or not isinstance(portfolios, dict):
        raise ValueError("Trades must be a list and portfolios must be an object")

    results = []
    for trade in trades:
        details = trade if isinstance(trade, dict) else {}
        results.append(
            {
                "portfolio_id": details.get("portfolio_id"),
                "security_id": details.get("security_id"),
                **evaluate_trade(trade, portfolios),
            }
        )
    return results
