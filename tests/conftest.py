import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--skip-stress",
        action="store_true",
        default=False,
        help="Skip tests marked with @pytest.mark.stress",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--skip-stress"):
        skip = pytest.mark.skip(reason="skipped via --skip-stress")
        for item in items:
            if "stress" in item.keywords:
                item.add_marker(skip)
