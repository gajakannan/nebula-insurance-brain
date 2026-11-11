"""Use the engine-migrated owned DB for the existing Neuron application image."""
import os
import subprocess

command=['docker','exec','-w','/app/brain','-e','BRAIN_TEST_POSTGRES_URL='+os.environ['BRAIN_TEST_POSTGRES_URL'],'-e','BRAIN_WORKER_DATABASE_URL='+os.environ['BRAIN_WORKER_DATABASE_URL'],'brain-f0007-remediation-81798e61-neuron-validation-1','python','-m','pytest','neuron/tests/integration/test_worker_cli_enqueue.py','neuron/tests/integration/test_document_process_recovery.py','neuron/tests/integration/test_document_delivery.py','-q','-p','no:cacheprovider','--import-mode=importlib','--junitxml=/evidence/artifacts/test-results/neuron-postgres-final.xml']
raise SystemExit(subprocess.run(command).returncode)
