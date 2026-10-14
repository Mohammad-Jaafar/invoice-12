import sys
from pathlib import Path

from app.schema import Invoice


def flatten(invoice: Invoice) -> dict:
    data = invoice.model_dump(mode="json")
    items = data.pop("items")
    for number, item in enumerate(items, start=1):
        for field, value in item.items():
            data[f"item{number}.{field}"] = value
    return data


def diff(expected: Invoice, actual: Invoice) -> list[tuple[str, object, object]]:
    want = flatten(expected)
    got = flatten(actual)
    names = list(want) + [name for name in got if name not in want]
    return [
        (name, want.get(name), got.get(name))
        for name in names
        if want.get(name) != got.get(name)
    ]


def load(path: str) -> Invoice:
    return Invoice.model_validate_json(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    rows = diff(load(sys.argv[1]), load(sys.argv[2]))
    if not rows:
        print("identical")
    for name, expected, actual in rows:
        print(f"{name}: expected={expected!r} actual={actual!r}")
