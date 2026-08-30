from verified_edge.cli import main


def test_cli_live_spike_stops_without_credential(monkeypatch, capsys):
    monkeypatch.delenv("UPSTOX_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(
        "sys.argv",
        [
            "ve-data",
            "upstox-spike",
            "--symbols",
            "RELIANCE",
            "--start",
            "2026-01-01",
            "--end",
            "2026-01-02",
        ],
    )
    assert main() == 2
    assert "live spike not run" in capsys.readouterr().err
