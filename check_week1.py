import hashlib
import importlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))

IMAGES = {".png", ".jpg", ".jpeg", ".webp"}
RESULTS: list[tuple[str, str]] = []
KEY_MARK = "sk" + "-ant"
KEY_PATTERNS = [KEY_MARK, r"AIza[0-9A-Za-z_-]{20,}", r"AQ\.[0-9A-Za-z_-]{20,}"]
KEY_NAMES = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY")


def record(status: str, name: str, hint: str = "") -> bool:
    RESULTS.append((status, name))
    print(f"[{status}] {name}")
    if status != "PASS" and hint:
        print(f"       -> {hint}")
    return status == "PASS"


def check(name: str, ok: bool, hint: str = "", soft: bool = False) -> bool:
    return record("PASS" if ok else ("WARN" if soft else "FAIL"), name, hint)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def git(*args: str) -> tuple[int, str]:
    try:
        done = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return 127, ""
    return done.returncode, done.stdout.strip()


def images_in(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(p for p in directory.iterdir() if p.suffix.lower() in IMAGES)


def load_module(name: str):
    try:
        return importlib.import_module(name), ""
    except Exception as error:
        return None, f"{type(error).__name__}: {error}"


def close(a: float, b: float, tolerance: float = 0.02) -> bool:
    return abs(a - b) <= tolerance


def load_invoices(directory: Path):
    schema, error = load_module("app.schema")
    if schema is None:
        return None, error
    invoices = {}
    for image in images_in(directory):
        path = image.with_suffix(".json")
        if path.exists():
            invoices[image.stem] = schema.Invoice.model_validate_json(read(path))
    return invoices, ""


def sound(invoice) -> bool:
    items_ok = all(close(i.quantity * i.unit_price, i.line_total) for i in invoice.items)
    return (
        items_ok
        and close(sum(i.line_total for i in invoice.items), invoice.subtotal)
        and close(invoice.subtotal * 0.05, invoice.vat_amount)
        and close(invoice.subtotal + invoice.vat_amount, invoice.total)
    )


def has_arabic(text: str) -> bool:
    return any("؀" <= ch <= "ۿ" for ch in text)


def secrets_clean() -> None:
    if not (ROOT / ".git").exists():
        check("git repository exists", False, "run: git init (or use uv init)")
        return
    pattern = "|".join(KEY_PATTERNS)
    code, tracked = git("grep", "-n", "-E", pattern)
    check("no API key text in tracked files", code == 1 and not tracked, "remove the key from the file, then delete the key in your provider dashboard and create a new one")
    code, history = git("log", "--all", "-p", "-G", pattern)
    check("no API key text anywhere in git history", not history, "the key was committed once: delete it in your provider dashboard and create a new one")


def day1() -> None:
    clean = ROOT / "data" / "clean"
    images = images_in(clean)
    check("data/clean has at least 10 images", len(images) >= 10, "run the generator: uv run python -m generator.generate --count 10")
    missing = [p.name for p in images if not p.with_suffix(".json").exists()]
    check("every image has a ground-truth JSON with the same name", bool(images) and not missing, f"missing JSON for: {missing[:3]}")
    invoices, error = load_invoices(clean)
    if invoices is None:
        check("app/schema.py imports and defines Invoice", False, error)
        invoices = {}
    else:
        check("app/schema.py imports and defines Invoice", True)
        check("all JSON files validate against the Invoice schema", len(invoices) == len(images) - len(missing) and len(invoices) > 0)
    unsound = [name for name, inv in invoices.items() if not sound(inv)]
    check("ground truth is arithmetically consistent (lines, 5% VAT, total)", bool(invoices) and not unsound, f"inconsistent: {unsound[:3]}")
    arabic = [n for n, inv in invoices.items() if has_arabic(inv.supplier_name) or any(has_arabic(i.description) for i in inv.items)]
    english = [n for n, inv in invoices.items() if not has_arabic(inv.supplier_name)]
    check("at least 3 Arabic invoices", len(arabic) >= 3, "the generator must produce Arabic supplier names and item descriptions")
    check("at least 3 English invoices", len(english) >= 3)
    bad_trn = [n for n, inv in invoices.items() if inv.supplier_trn is not None and not (inv.supplier_trn.isascii() and inv.supplier_trn.isdigit() and len(inv.supplier_trn) == 15)]
    check("TRN values use 15 Western digits", bool(invoices) and not bad_trn, f"bad TRN in: {bad_trn[:3]}")
    small = []
    for image in images:
        head = image.read_bytes()[:24]
        if image.suffix.lower() == ".png":
            if head[:8] != b"\x89PNG\r\n\x1a\n" or int.from_bytes(head[16:20], "big") < 400:
                small.append(image.name)
    check("PNG files are valid and wide enough to read", bool(images) and not small, f"suspicious: {small[:3]}")
    gitignore = read(ROOT / ".gitignore")
    check(".gitignore lists .env", re.search(r"^\.env\s*$", gitignore, re.M) is not None, "add a line containing exactly: .env")
    if (ROOT / ".git").exists():
        code, listed = git("ls-files", ".env")
        check(".env is not tracked by git", not listed)
        code, remotes = git("remote")
        check("GitHub remote is configured", bool(remotes), "git remote add origin <your repo url>", soft=True)
        code, count = git("rev-list", "--count", "HEAD")
        check("at least one commit exists", code == 0 and count.isdigit() and int(count) >= 1, "git add . && git commit -m \"day 1\"")
    else:
        check("git repository exists", False, "run: git init")
    log = read(ROOT / "LEARNING_LOG.md")
    check("LEARNING_LOG.md has at least one entry", len(log.strip()) >= 150, "write your 3 lines about what you built today")


def day2() -> None:
    validator, error = load_module("app.validator")
    check("app/validator.py imports", validator is not None, error)
    extractor_text = read(ROOT / "app" / "extractor.py")
    check("app/extractor.py exists", bool(extractor_text), "ask your assistant for it (prompt 1, day 2)")
    check("extractor defines extract_file", "def extract_file" in extractor_text, "the function must be named extract_file(path, model)")
    structured = ("output_format" in extractor_text and "parse" in extractor_text) or "response_schema" in extractor_text
    check("extractor uses structured outputs (output_format or response_schema)", structured, "Claude: client.messages.parse(..., output_format=Invoice). Gemini: response_schema=Invoice", soft=True)
    env = read(ROOT / ".env")
    key = re.search(r"(?m)^(?:GEMINI_API_KEY|GOOGLE_API_KEY|ANTHROPIC_API_KEY)\s*=\s*(\S+)", env)
    check(".env contains an API key line", bool(key and len(key.group(1)) > 10), "create .env with a line: GEMINI_API_KEY=your-key (or ANTHROPIC_API_KEY=your-key)")
    out = ROOT / "data" / "out"
    outputs = sorted(out.glob("*.json")) if out.exists() else []
    check("data/out has extraction results for at least 10 invoices", len(outputs) >= 10, "uv run python -m eval.extract_all --dir data/clean --out data/out")
    schema, _ = load_module("app.schema")
    if schema and outputs:
        valid = 0
        for path in outputs:
            try:
                schema.Invoice.model_validate_json(read(path))
                valid += 1
            except Exception:
                pass
        check("all files in data/out are valid Invoice JSON", valid == len(outputs), f"{len(outputs) - valid} invalid file(s)")
    if validator is None or schema is None:
        return
    invoices, _ = load_invoices(ROOT / "data" / "clean")
    if not invoices:
        return
    verdicts = [validator.validate(inv).status for inv in invoices.values()]
    check("validator says ok on every correct ground-truth invoice", all(v == "ok" for v in verdicts), f"{sum(v != 'ok' for v in verdicts)} false alarm(s)")
    sample = next(iter(invoices.values()))
    broken_lines = sample.model_copy(update={"items": [sample.items[0].model_copy(update={"line_total": sample.items[0].line_total + 5}), *sample.items[1:]]})
    check("validator flags a broken line total", validator.validate(broken_lines).status == "needs_review", "the sum-of-lines rule is missing or wrong")
    check("validator returns problems as a list of strings", bool(validator.validate(broken_lines).problems))
    tests = sorted((ROOT / "tests").glob("test_*.py")) if (ROOT / "tests").exists() else []
    check("tests/ contains test files", bool(tests), "ask for pytest tests (prompt 2, day 2)")
    if tests:
        done = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x"], capture_output=True, text=True, cwd=ROOT, encoding="utf-8", errors="replace")
        tail = done.stdout.strip().splitlines()[-1] if done.stdout.strip() else done.stderr.strip()[-200:]
        check("pytest passes", done.returncode == 0, tail)
    log = read(ROOT / "LEARNING_LOG.md")
    check("LEARNING_LOG.md has at least 2 dated entries", len(re.findall(r"(?im)^#+\s*(day|\d{4}-)", log)) >= 2 or len(log) > 500, "one entry per day, 3 lines each", soft=True)


def day3() -> None:
    clean = ROOT / "data" / "clean"
    check("data/clean has at least 30 invoices", len(images_in(clean)) >= 30, "uv run python -m generator.generate --count 30")
    score, error = load_module("eval.score")
    check("eval/score.py imports", score is not None, error)
    validator, _ = load_module("app.validator")
    invoices, _ = load_invoices(clean)
    if score is not None and invoices:
        sample = next(iter(invoices.values()))
        same = score.score_invoice(sample, sample)
        check("scoring an invoice against itself gives 100% on every field", isinstance(same, dict) and len(same) >= 6 and all(same.values()), "score_invoice(expected, actual) must return a dict of field -> bool")
        changed = sample.model_copy(update={"total": sample.total + 5})
        res = score.score_invoice(sample, changed)
        check("scoring detects a wrong total", isinstance(res, dict) and not all(res.values()))
        renamed = sample.model_copy(update={"invoice_number": sample.invoice_number + "9"})
        res = score.score_invoice(sample, renamed)
        check("scoring detects a wrong invoice number", isinstance(res, dict) and not all(res.values()))
    check("eval/run_eval.py exists", (ROOT / "eval" / "run_eval.py").exists())
    results = read(ROOT / "eval" / "results.md")
    check("eval/results.md exists with real percentages", results.count("%") >= 6, "run the evaluation and paste the table into eval/results.md")
    check("results.md reports validator catches and false alarms", bool(re.search(r"(?i)false|caught|flagged|كاذب", results)), "write both numbers: errors caught, false alarms", soft=True)
    if validator is None or not invoices:
        return
    sample = next(inv for inv in invoices.values() if inv.supplier_trn)
    mutations = {
        "wrong line total": sample.model_copy(update={"items": [sample.items[0].model_copy(update={"line_total": sample.items[0].line_total + 5}), *sample.items[1:]]}),
        "wrong subtotal": sample.model_copy(update={"subtotal": sample.subtotal + 5}),
        "wrong VAT": sample.model_copy(update={"vat_amount": sample.vat_amount + 5}),
        "wrong total": sample.model_copy(update={"total": sample.total + 5}),
        "14-digit TRN": sample.model_copy(update={"supplier_trn": sample.supplier_trn[:-1]}),
        "TRN with letters": sample.model_copy(update={"supplier_trn": "A" + sample.supplier_trn[1:]}),
    }
    for label, mutated in mutations.items():
        check(f"validator flags: {label}", validator.validate(mutated).status == "needs_review", "the matching rule is missing")
    arabic_digits = sample.supplier_trn.translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))
    check("validator accepts a TRN written in Arabic-Indic digits", validator.validate(sample.model_copy(update={"supplier_trn": arabic_digits})).status == "ok", "normalize digits before checking length")
    check("validator tolerates a 0.01 rounding difference", validator.validate(sample.model_copy(update={"total": sample.total + 0.01})).status == "ok", "tolerance should be 0.02", soft=True)
    verdicts = [validator.validate(inv).status for inv in invoices.values()]
    check("no false alarms on the correct ground truth", all(v == "ok" for v in verdicts), f"{sum(v != 'ok' for v in verdicts)} false alarm(s)")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def day4() -> None:
    clean = ROOT / "data" / "clean"
    scanned = ROOT / "data" / "scanned"
    images = images_in(scanned)
    check("data/scanned has at least 30 images", len(images) >= 30, "uv run python -m generator.degrade")
    mismatched = []
    for image in images:
        mine, original = image.with_suffix(".json"), clean / f"{image.stem}.json"
        if not mine.exists() or not original.exists() or digest(mine) != digest(original):
            mismatched.append(image.name)
    check("scanned ground-truth JSON files are identical copies of the clean ones", not mismatched, f"differs or missing: {mismatched[:3]}")
    cv2, error = load_module("cv2")
    if cv2 is None:
        check("opencv is installed", False, "uv add opencv-python-headless")
        return
    unchanged, unreadable = [], []
    for image in images[:30]:
        original = next((p for p in images_in(clean) if p.stem == image.stem), None)
        a = cv2.imread(str(image), cv2.IMREAD_GRAYSCALE)
        if a is None:
            unreadable.append(image.name)
            continue
        if original is None:
            continue
        b = cv2.imread(str(original), cv2.IMREAD_GRAYSCALE)
        if b is None:
            continue
        a = cv2.resize(a, (b.shape[1], b.shape[0]))
        if float(abs(a.astype("int16") - b.astype("int16")).mean()) < 1.0:
            unchanged.append(image.name)
    check("every scanned image opens", not unreadable, f"unreadable: {unreadable[:3]}")
    check("scanned images really differ from the clean ones", len(unchanged) <= 2, f"almost identical to the clean image: {unchanged[:3]}")
    results = read(ROOT / "eval" / "results.md")
    check("results.md compares clean vs scanned", bool(re.search(r"(?i)scan", results)) and bool(re.search(r"(?i)clean", results)), "add both result tables")
    check("results.md contains an error analysis", bool(re.search(r"(?i)error|failure|فشل|خطأ|أخطاء", results)) and len(results) > 700, "3 error types, an example for each, your hypothesis", soft=True)
    check("results.md records the improvement experiment", bool(re.search(r"(?i)clahe|experiment|prompt|تجربة", results)), "write what you changed and the measured effect", soft=True)


def day5() -> None:
    results = read(ROOT / "eval" / "results.md").lower()
    models = set(re.findall(r"(?:claude|gemini)-[a-z0-9.-]+", results))
    two_models = len(models) >= 2 or ("sonnet" in results and "haiku" in results)
    check("results.md compares two models", two_models, "run the evaluation with a second model and record both tables, writing the exact model names")
    check("results.md has a written decision", "decision" in results or "قرار" in results, "add a section named Decision (4 lines)")
    check("results.md mentions cost per invoice", bool(re.search(r"cost|\$", results)))
    main, error = load_module("app.main")
    if main is None:
        check("app/main.py imports", False, error)
        return
    check("app/main.py imports", True)
    paths = main.app.openapi().get("paths", {})
    check("POST /extract exists", "post" in paths.get("/extract", {}), "define @app.post('/extract')")
    try:
        from fastapi.testclient import TestClient

        client = TestClient(main.app)
        bad = client.post("/extract", files={"file": ("note.txt", b"hello", "text/plain")})
        check("a non-image upload is rejected with 400", bad.status_code == 400, f"got {bad.status_code}")
        health = client.get("/health")
        check("GET /health returns 200", health.status_code == 200, "add a /health route", soft=True)
    except Exception as exc:
        check("FastAPI test client works", False, f"{type(exc).__name__}: {exc}  (uv add \"fastapi[standard]\")")
    check("data/scanned exists for the model comparison", len(images_in(ROOT / "data" / "scanned")) >= 30)


def day6() -> None:
    readme = read(ROOT / "README.md")
    lower = readme.lower()
    check("README.md is substantial", len(readme) >= 1500, "aim for 2000+ characters")
    headings = [line.lower() for line in readme.splitlines() if line.startswith("#")]
    groups = {
        "problem": ("problem",),
        "results": ("result", "accuracy", "evaluation"),
        "how it works": ("how it works", "architecture", "pipeline"),
        "how to run": ("run", "setup", "quick start", "getting started", "usage", "install"),
        "limitations": ("limit", "known issues", "weakness"),
    }
    for label, words in groups.items():
        check(f"README has a '{label}' section", any(any(w in h for w in words) for h in headings), "add a heading for it")
    check("README says the data is synthetic", "synthetic" in lower, "state it plainly in the results section")
    check("README links to the demo video", bool(re.search(r"https?://", readme)) and bool(re.search(r"(?i)video|demo|loom|youtu", readme)), "upload the 2-minute video and link it", soft=True)
    env_example = read(ROOT / ".env.example")
    names = [n for n in KEY_NAMES if n in env_example]
    leaked = any(re.search(pattern, env_example) for pattern in KEY_PATTERNS)
    empty = all(re.search(rf"(?m)^{n}\s*=\s*(your-key-here)?\s*$", env_example) for n in names)
    check(".env.example exists with an empty key", bool(names) and not leaked and empty, "GEMINI_API_KEY=  (no value, or your-key-here)")
    secrets_clean()
    if (ROOT / ".git").exists():
        code, listed = git("ls-files")
        names = listed.splitlines()
        check("data/ and .env are not tracked", not any(n.startswith("data/") or n == ".env" for n in names), "git rm -r --cached data .env")
        code, dirty = git("status", "--porcelain")
        check("working tree is committed", not dirty, "git add . && git commit -m \"...\"")
        code, ahead = git("log", "@{u}..HEAD", "--oneline")
        check("everything is pushed to GitHub", code == 0 and not ahead, "git push", soft=True)
        code, url = git("remote", "get-url", "origin")
        if code == 0 and url:
            with tempfile.TemporaryDirectory() as tmp:
                done = subprocess.run(["git", "clone", "--quiet", url, tmp + "/clone"], capture_output=True, text=True)
                if done.returncode != 0:
                    check("fresh clone from GitHub works", False, "could not clone (private repo or not pushed?)", soft=True)
                else:
                    clone = Path(tmp) / "clone"
                    needed = ["README.md", "app/schema.py", "app/extractor.py", "app/validator.py", "app/main.py", "generator", "eval/score.py", "pyproject.toml"]
                    absent = [n for n in needed if not (clone / n).exists()]
                    check("fresh clone contains the project files", not absent, f"missing in the repo: {absent}")
                    check("fresh clone does not contain .env", not (clone / ".env").exists())


DAYS = {1: day1, 2: day2, 3: day3, 4: day4, 5: day5, 6: day6}


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else "1"
    last = 6 if arg == "all" else int(arg)
    for number in range(1, min(last, 6) + 1):
        print(f"\n=== Day {number} ===")
        DAYS[number]()
    failed = sum(1 for status, _ in RESULTS if status == "FAIL")
    warned = sum(1 for status, _ in RESULTS if status == "WARN")
    passed = sum(1 for status, _ in RESULTS if status == "PASS")
    print(f"\nPASS {passed}   WARN {warned}   FAIL {failed}")
    print("ALL REQUIRED CHECKS PASSED" if not failed else "FIX THE FAIL LINES, THEN RUN AGAIN")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
