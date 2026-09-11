from __future__ import annotations

from pathlib import Path

from brain_security.casbin_adapter import CasbinAuthorizationAdapter


def test_tenant_member_can_read_content_artifact_in_same_kb(
    model_path: Path, policy_path: Path
) -> None:
    adapter = CasbinAuthorizationAdapter(model_path, policy_path)

    assert adapter.enforce("TenantMember", "kb-1", "content_artifact", "kb-1", "read") is True


def test_tenant_member_cannot_read_across_knowledge_bases(
    model_path: Path, policy_path: Path
) -> None:
    adapter = CasbinAuthorizationAdapter(model_path, policy_path)

    assert adapter.enforce("TenantMember", "kb-1", "content_artifact", "kb-2", "read") is False


def test_reviewer_can_annotate_review_task(model_path: Path, policy_path: Path) -> None:
    adapter = CasbinAuthorizationAdapter(model_path, policy_path)

    assert adapter.enforce("Reviewer", "kb-1", "review_task", "kb-1", "annotate") is True


def test_tenant_member_cannot_annotate_review_task(model_path: Path, policy_path: Path) -> None:
    """TenantMember has `read` on review_task, not `annotate` — role separation."""
    adapter = CasbinAuthorizationAdapter(model_path, policy_path)

    assert adapter.enforce("TenantMember", "kb-1", "review_task", "kb-1", "annotate") is False


def test_service_principal_can_commit_fact_slot(model_path: Path, policy_path: Path) -> None:
    adapter = CasbinAuthorizationAdapter(model_path, policy_path)

    assert adapter.enforce("ServicePrincipal", "kb-1", "fact_slot", "kb-1", "commit") is True


def test_reviewer_cannot_commit_fact_slot(model_path: Path, policy_path: Path) -> None:
    adapter = CasbinAuthorizationAdapter(model_path, policy_path)

    assert adapter.enforce("Reviewer", "kb-1", "fact_slot", "kb-1", "commit") is False


def test_policy_hash_is_stable_sha256_of_policy_csv(model_path: Path, policy_path: Path) -> None:
    import hashlib

    adapter = CasbinAuthorizationAdapter(model_path, policy_path)

    assert adapter.policy_hash == hashlib.sha256(policy_path.read_bytes()).hexdigest()
