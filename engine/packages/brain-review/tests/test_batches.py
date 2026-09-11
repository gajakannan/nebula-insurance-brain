from __future__ import annotations

from uuid import uuid4

import pytest
from brain_review.batches import assemble_batch

from .conftest import make_review_item


def test_assemble_batch_groups_item_ids() -> None:
    items = [make_review_item(), make_review_item()]
    principal_id = uuid4()

    batch = assemble_batch(items, assembling_principal_id=principal_id)

    assert set(batch.review_item_ids) == {item.id for item in items}
    assert batch.assembling_principal_id == principal_id


def test_assemble_batch_rejects_empty_list() -> None:
    with pytest.raises(ValueError, match="zero review items"):
        assemble_batch([], assembling_principal_id=uuid4())
