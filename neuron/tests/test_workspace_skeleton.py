"""Smoke test for the neuron/ uv workspace (F0001-S0001).

neuron/packages/ is intentionally empty until F0001-S0003 adds the ingestion,
extraction, and interpretation packages. This test proves the workspace's
pytest/coverage wiring runs end to end before any AI code lands.
"""


def test_neuron_workspace_pytest_is_wired() -> None:
    assert True
