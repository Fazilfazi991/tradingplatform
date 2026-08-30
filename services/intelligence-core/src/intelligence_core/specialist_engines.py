from intelligence_core.models import FrozenModel


class SpecialistEngineRecord(FrozenModel):
    engine_id: str
    version: str
    status: str
    inputs: tuple[str, ...]
    output_contract: str
    causal_requirements: tuple[str, ...]
    validation_status: str
    live_data_status: str
    predictive_validation_status: str = "NOT_STARTED"


def specialist_engine_registry() -> tuple[SpecialistEngineRecord, ...]:
    definitions = (
        ("TECHNICAL", "market observations", "TechnicalEvidence"),
        ("HISTORICAL", "chronological research partitions", "HistoricalEvidence"),
        ("NEWS_EVENT", "causal information events", "NewsEvidenceOutput"),
        ("MACRO_GLOBAL", "macro observations and cross-market state", "MacroEvidence"),
        ("FUNDAMENTAL", "fundamental snapshots", "FundamentalEvidence"),
        ("PSYCHOLOGY", "psychology snapshots", "PsychologyEvidence"),
        ("FLOW_DERIVATIVES", "flow and derivatives snapshots", "FlowDerivativesEvidence"),
    )
    return tuple(SpecialistEngineRecord(
        engine_id=engine, version="1", status="ENGINEERING_READY",
        inputs=(inputs,), output_contract=output,
        causal_requirements=("available_at <= cutoff", "point-in-time source version"),
        validation_status="FIXTURE_VALIDATED", live_data_status="INTERNAL_OR_FIXTURE_ONLY")
        for engine, inputs, output in definitions)
