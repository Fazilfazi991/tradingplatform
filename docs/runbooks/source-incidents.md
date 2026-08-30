# Source incident runbook

Incident types include stale source, parser schema change, entity-resolution spike, duplicate anomaly,
authentication failure, rate-limit breach, volume drop, missed schedule, and snapshot failure.

Transient network faults may retry within the declared policy. Repeated parser/source failures degrade
health and open the circuit; raw artifacts remain preserved while canonical promotion stops. Automatic
reactivation is not permitted after one success. Inspect multiple healthy cycles, acknowledge the
incident, reset conservatively, then replay preserved artifacts. Workers never edit collector code.

Escalate code/schema repair to a controlled Codex or human maintenance workflow with evidence,
affected parser version, impacted tests, and rollback plan.
