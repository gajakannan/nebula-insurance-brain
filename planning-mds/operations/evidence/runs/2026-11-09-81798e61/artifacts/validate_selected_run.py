"""Validate the explicitly selected in-progress run with the pinned framework checks.

The pinned CLI skips nonterminal Active Features even with --run-id (validate.py
lines3789-3791). Invoke its unchanged governed-row validator directly so PASS must
mean one run was actually checked. G6/G7 reentry also has a documented, narrowly
scoped validator defect: an older approved pointer must remain until G8, but
resolve_run rejects it before loading this candidate. For exactly that known
prior run, continue all unchanged checks on the explicit candidate and apply
the framework's recorded validator-defect disposition. Closeout uses the CLI.
"""
import importlib.util
from pathlib import Path
import sys

framework=Path('/home/gajap/uSandbox/repos/nebula/nebula-agents')
path=framework/'agents/product-manager/scripts/validate-feature-evidence.py'
spec=importlib.util.spec_from_file_location('selected_feature_evidence',path)
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)
root=Path('/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain')
stage=sys.argv[1] if len(sys.argv)>1 else 'G3'
args=module.build_parser().parse_args(['--product-root',str(root),'--feature','F0007','--run-id','2026-11-09-81798e61','--stage',stage])
rule,patterns=module.validate_secret_patterns(root)
assert not rule and module.validate_path_class_extensions(root)
result=module.Result(stage=stage,product_root=root,effective_date=module.parse_effective_date(None))
rows=module.load_registry(root,result)
scanner=module.build_secret_scanner(patterns)
if stage not in {'G6','G7'}:
    module.validate_governed_row(rows['F0007'],result,stage,args.run_id,scanner)
else:
    import json
    row=rows['F0007']
    folder=root/'planning-mds/operations/evidence/runs'/args.run_id
    manifest_path=folder/'evidence-manifest.json'
    candidate=json.loads(manifest_path.read_text())
    latest=json.loads((root/'planning-mds/operations/evidence/features/F0007-factslot-model/latest-run.json').read_text())
    assert candidate['status']=='in-progress'
    assert latest['run_id']==candidate['remediation_of']
    assert candidate['gate_results']['approval']['result']=='APPROVED'
    module.resolve_run(row,stage,args.run_id,result)
    manifest=module.validate_manifest(row,args.run_id,manifest_path,result,stage,scanner)
    assert manifest is not None
    required=module.parse_status_required_roles(row,result)
    module.validate_required_artifacts(row,manifest,folder,stage,result)
    module.validate_gate_decisions(folder,manifest,stage,row,result)
    module.validate_lifecycle_gates(folder,row,result)
    module.validate_commands_log(folder,manifest,scanner,row,result)
    module.validate_role_and_gate_results(row,manifest,folder,stage,result,required)
    module.validate_status_md(row,manifest,folder,stage,result)
    module.validate_recommendations_in_role_reports(row,manifest,folder,stage,result)
    module.validate_coverage_waiver_acceptance(row,manifest,folder,stage,result)
    module.validate_validator_defect_waiver(row,manifest,folder,stage,result)
    module.validate_cross_artifact_consistency(row,manifest,manifest_path,folder,stage,result)
    module.apply_validator_defect_downgrades(result,manifest)
    if not result.errors:result.features_validated=1
exit_code=1 if result.errors or result.features_validated!=1 else 0
raise SystemExit(module.output_result(result,args,exit_code))
