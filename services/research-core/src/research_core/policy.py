from __future__ import annotations

from dataclasses import dataclass

from research_core.objects import ResearchMode

REQUIRED_FORMAL_GATES = (
    "live_market_data_validation",
    "postgres_runtime_verification",
    "point_in_time_universe",
    "corporate_action_correctness",
    "second_source_acceptance",
)


class ResearchGateError(PermissionError):
    pass


@dataclass(frozen=True)
class ResearchGatePolicy:
    gates: dict[str, bool]

    @classmethod
    def current(cls) -> ResearchGatePolicy:
        return cls({gate: False for gate in REQUIRED_FORMAL_GATES})

    def authorize(self, mode: ResearchMode) -> None:
        if mode == ResearchMode.ENGINEERING_FIXTURE:
            return
        missing = [gate for gate in REQUIRED_FORMAL_GATES if not self.gates.get(gate, False)]
        if missing:
            raise ResearchGateError(
                f"{mode.value} blocked; missing readiness gates: {', '.join(missing)}"
            )
