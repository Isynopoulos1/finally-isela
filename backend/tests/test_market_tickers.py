from market.tickers import normalize, normalize_all


def test_normalize_strips_and_uppercases():
    assert normalize("  aapl ") == "AAPL"


def test_normalize_empty_string():
    assert normalize("   ") == ""


def test_normalize_all_deduplicates_preserving_first_occurrence_order():
    assert normalize_all(["msft", "AAPL", " msft "]) == ["MSFT", "AAPL"]


def test_normalize_all_drops_blanks():
    assert normalize_all(["aapl", "  ", "", "tsla"]) == ["AAPL", "TSLA"]


def test_normalize_all_empty_list():
    assert normalize_all([]) == []
