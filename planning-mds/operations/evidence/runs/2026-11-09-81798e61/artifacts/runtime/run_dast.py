"""Run the installed API scanner against only this run's fresh owned database/API."""
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

out=Path('/evidence/artifacts/security/dast')
out.mkdir(parents=True,exist_ok=True)
host_out='/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-09-81798e61/artifacts/security/dast'
port=8765
try:
    urllib.request.urlopen(f'http://127.0.0.1:{port}/openapi.json',timeout=1)
except OSError:
    pass
else:
    raise RuntimeError('Refusing to scan an existing server on the validation port')
with (out/'uvicorn.log').open('w') as serverlog:
    api=subprocess.Popen([sys.executable,'-m','uvicorn','brain_api.app:create_app','--factory','--host','0.0.0.0','--port',str(port)],stdout=serverlog,stderr=subprocess.STDOUT,env=os.environ)
    try:
        for _ in range(30):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/openapi.json',timeout=1) as response:
                    if response.status==200:break
            except OSError:time.sleep(1)
        else:raise RuntimeError('Fresh API did not become ready')
        target=f'http://brain-f0007-remediation-81798e61-engine-validation-1:{port}/openapi.json'
        cmd=['docker','run','--rm','--network','nebula-insurance-brain_default','-u','1000:1000','-v',host_out+':/zap/wrk:rw','sha256:8d387b1a63e3425beef4846e39719f5af2a787753af2d8b6558c6257d7a577a2','zap-api-scan.py','-t',target,'-f','openapi','-r','api-scan.html','-J','api-scan.json','-T','4','-z','-silent -config autoupdate.checkOnStart=false -config autoupdate.installAddonUpdates=false -config autoupdate.installScannerRules=false']
        with (out/'zap.out').open('w') as log:result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
        print('Fresh API/OpenAPI ready; ZAP exit',result.returncode)
        print((out/'zap.out').read_text()[-5000:])
        raise SystemExit(result.returncode)
    finally:
        api.terminate()
        try:api.wait(timeout=10)
        except subprocess.TimeoutExpired:api.kill();api.wait()
