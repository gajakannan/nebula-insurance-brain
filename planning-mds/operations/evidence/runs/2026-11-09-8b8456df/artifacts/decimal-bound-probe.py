"""Bounded local review probe; never invokes an API or a database."""
import resource

from brain_domain.fact_values import ValueRejected, canonical_decimal

resource.setrlimit(resource.RLIMIT_AS, (128 * 1024 * 1024, 128 * 1024 * 1024))
try:
    canonical_decimal('1e999999999')
except MemoryError:
    print('CONFIRMED: canonical expansion reaches the process memory cap before named validation')
except ValueRejected:
    print('Named validation rejected before memory exhaustion')
    raise SystemExit(1)
else:
    raise AssertionError('Unexpected accepted result')
