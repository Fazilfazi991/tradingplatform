import subprocess
from pathlib import Path

from research_core.experiment import generate_report, run_synthetic_experiment


def main() -> None:
    code_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    root = Path("research")
    for name, planted in (
        ("synthetic-edge-engineering", True),
        ("synthetic-null-engineering", False),
    ):
        result = run_synthetic_experiment(
            planted_edge=planted,
            output_root=root / "experiments" / name,
            code_sha=code_sha,
        )
        report = generate_report(result, root / "reports" / f"{name}.md")
        metrics = result["metrics"]
        print(
            f"{name}: ROC_AUC={metrics['roc_auc']:.4f} BRIER={metrics['brier']:.4f} REPORT={report}"
        )


if __name__ == "__main__":
    main()
