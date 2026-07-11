from main import build_parser, main


def test_parser_supports_requested_options() -> None:
    args = build_parser().parse_args([
        "--days-back", "3",
        "--final-count", "21",
        "--max-candidates", "50",
        "--no-llm",
        "--output-format", "csv", "markdown",
    ])

    assert args.days_back == 3
    assert args.final_count == 21
    assert args.max_candidates == 50
    assert args.no_llm is True
    assert args.output_format == ["csv", "markdown"]


def test_main_rejects_reversed_date_range_without_network() -> None:
    exit_code = main([
        "--week-start", "2026-07-12",
        "--week-end", "2026-07-06",
        "--no-llm",
    ])

    assert exit_code == 2
