"""F0012 foundation ontology toolchain (ADR-0081).

Offline: `authoring` validates module files, `compiler` builds content-addressed
release locks, `semantics` computes the supported inference closure and
`rdf_export` writes Turtle and JSON-LD. Runtime: `service` installs, reports,
reviews and activates releases under the existing authorization service; `cli`
is the command-line entry point.
"""

COMPILER_VERSION = "brain-ontology-compiler/1"
