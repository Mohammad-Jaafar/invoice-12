PRICES = {
    "gemini-3.8-flash": (0.75, 3.75),
}


def cost(model: str, input_tokens: float, output_tokens: float) -> float | None:
    if model not in PRICES:
        return None
    input_price, output_price = PRICES[model]
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000
