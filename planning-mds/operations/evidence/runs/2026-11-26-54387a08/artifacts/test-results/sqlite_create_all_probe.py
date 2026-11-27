"""F0012: the neuron recovery suite's SQLite `create_all` (same exclusions) accepts the
new ontology ORM tables (`ARRAY` columns use their SQLite JSON variant)."""
from sqlalchemy import create_engine, inspect
from brain_persistence.models import Base

excluded = {"fact_slot", "fact_slot_qualifier", "canonical_fact_version", "canonical_fact_change", "outbox_event"}
engine = create_engine("sqlite://")
Base.metadata.create_all(engine, tables=[t for t in Base.metadata.sorted_tables if t.name not in excluded])
names = set(inspect(engine).get_table_names())
ontology = sorted(n for n in names if n.startswith("ontology_"))
assert len(ontology) == 8, ontology
print({"sqlite_tables": len(names), "ontology_tables": ontology})
