"""CPU-only validation of the frozen adaptive-off diagnostic control."""
import hashlib,importlib.util,json,re,shlex,subprocess,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[2]
D=R/'tools/fastfix'
def load(name):return json.loads((D/name).read_text())
def digest(path):
    with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
class Control(unittest.TestCase):
    def test_only_inference_change_is_swap_limit(self):
        baseline=load('aplan-runtime.json');static=load('aplan-control-static.json');adaptive=load('aplan-control-adaptive.json')
        self.assertEqual(adaptive['args'],baseline['args'])
        self.assertEqual(static['args'],baseline['args']+['--adapt-swaps','0'])
        for profile in (static,adaptive):
            self.assertEqual({k:v for k,v in profile.items() if k not in ('args','log')},{k:v for k,v in baseline.items() if k not in ('args','log')})
            self.assertEqual(profile['args'].count('--expert-cache'),1)
            self.assertEqual(profile['args'][profile['args'].index('--expert-cache')+1],'8098')
            self.assertNotIn('--expert-profile-save',profile['args'])
    def test_original_artifacts_and_engine_sources_unchanged(self):
        manifest=load('aplan-candidate.json')
        for path,expected in manifest['files'].items():self.assertEqual(digest(R/path),expected,path)
    def test_archive_has_active_defaults(self):
        x=json.loads((R/'logs/fastfix/p0-window-01/mtp-on-container.json').read_text());x=x[0] if isinstance(x,list) else x
        args=shlex.split(x['Config']['Cmd'][0])[3:]
        self.assertEqual(args,load('aplan-control-adaptive.json')['args'])
        self.assertNotIn('--adapt-swaps',args);self.assertNotIn('--adapt-every',args)
        source=(R/'sycl/src/program/generate.cpp').read_text()
        self.assertRegex(source,r'int adapt_every = 4;');self.assertRegex(source,r'int adapt_swaps = 96;')
    def test_real_serving_guards_disable_adaptation(self):
        source=(R/'sycl/src/program/generate.cpp').read_text()
        self.assertIn('o.adapt_swaps = std::atoi(next("--adapt-swaps"))',source)
        # Evaluate the actual source gate for 4/0 and original 4/96, not a different toggle.
        match=re.search(r'if \((o\.adapt_every > 0 && o\.adapt_swaps > 0)\) drive\.d\.usage\.assign',source)
        self.assertIsNotNone(match)
        predicate=match[1].replace('o.adapt_every','every').replace('o.adapt_swaps','swaps').replace('&&','and')
        self.assertFalse(eval(predicate,{'__builtins__':{}},{'every':4,'swaps':0}))
        self.assertTrue(eval(predicate,{'__builtins__':{}},{'every':4,'swaps':96}))
        self.assertIn('if (!drive.d.usage.empty() && ((rounds + 1) % o.adapt_every) == 0)',source)
        self.assertIn('if (pending.empty()) return;',source)
        self.assertIn('if (!d.usage.empty())', (R/'sycl/src/core/expert_source.cpp').read_text())
    def test_same_prompt_mtp_and_safety(self):
        request=load('aplan-request.json');self.assertEqual(request['max_tokens'],1536)
        self.assertEqual(request['seed'],42);self.assertEqual(request['temperature'],0)
        baseline=load('aplan-runtime.json')
        self.assertEqual(baseline['args'][baseline['args'].index('--spec')+1],'4')
        wrapper=(D/'p0-engine-wrapper.py').read_text()
        for s in ('STRATA_ARENA_ALIAS_CHECK=1','STRATA_HOST_UNCACHED=1','STRATA_VERIFY_DEVICE_PLAN=1','STRATA_APLAN_DIAG=1'):
            self.assertIn(s,wrapper)
        self.assertIn('wait_and_throw()', (R/'sycl/src/core/verify.cpp').read_text())
    def test_fixed_window_and_second_arm_admission(self):
        spec=importlib.util.spec_from_file_location('plan',D/'aplan-control-plan.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertEqual(module.TOTAL,900);self.assertEqual(module.EXPERIMENT_END,600)
        self.assertTrue(module.admit_arm(210));self.assertFalse(module.admit_arm(211))
        self.assertFalse(module.admit_arm(600));self.assertFalse(module.admit_arm(-1))
        self.assertEqual(module.TOTAL-module.EXPERIMENT_END,300)
    def test_plan_dry_run_has_no_lifecycle_or_gpu(self):
        result=subprocess.run([sys.executable,'-B',str(D/'aplan-control-plan.py')],check=True,capture_output=True,text=True)
        p=json.loads(result.stdout)
        self.assertFalse(p['gpu_execution']);self.assertFalse(p['production_lifecycle_actions'])
        self.assertEqual(p['last_arm_admission_seconds'],210)
if __name__=='__main__':unittest.main()
