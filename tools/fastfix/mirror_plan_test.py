import importlib.util,json,subprocess,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[2];D=R/'tools/fastfix'
spec=importlib.util.spec_from_file_location('plan',D/'mirror-repair-plan.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Plan(unittest.TestCase):
    def test_same_original_profile(self):
        a=json.loads((D/'aplan-runtime.json').read_text());b=json.loads((D/'mirror-repair-runtime.json').read_text())
        self.assertEqual({k:v for k,v in a.items() if k!='log'},{k:v for k,v in b.items() if k!='log'})
        self.assertNotIn('--adapt-swaps',b['args']);self.assertNotIn('--expert-profile-save',b['args'])
    def test_exact_prompt_only_longer_cap(self):
        a=json.loads((D/'aplan-request.json').read_text());b=json.loads((D/'mirror-repair-request.json').read_text())
        self.assertEqual(b['max_tokens'],2048);self.assertEqual({k:v for k,v in a.items() if k!='max_tokens'},{k:v for k,v in b.items() if k!='max_tokens'})
    def test_fixed_recovery_reserve(self):
        self.assertEqual(m.TOTAL-m.EXPERIMENT_END,300);self.assertLessEqual(sum(s for _,s in m.STAGES),m.EXPERIMENT_END)
    def test_request_admission(self):
        self.assertTrue(m.admit(570,240));self.assertFalse(m.admit(571,240));self.assertFalse(m.admit(-1,240))
    def test_short_requests_admission(self):
        self.assertTrue(m.admit(720,90));self.assertFalse(m.admit(721,90));self.assertFalse(m.admit(0,-1))
    def test_dry_run_cannot_stop_or_run_gpu(self):
        p=subprocess.run([sys.executable,'-B',str(D/'mirror-repair-plan.py')],check=True,capture_output=True,text=True)
        o=json.loads(p.stdout);self.assertFalse(o['gpu_execution']);self.assertFalse(o['production_lifecycle_actions'])
        self.assertIn('PENDING',o['authorization'])
    def test_actual_stage_order(self):
        self.assertIn('safety',m.STAGES[0][0]);self.assertIn('GGUF',m.STAGES[2][0]);self.assertIn('Adaptive ON',m.STAGES[3][0])
if __name__=='__main__':unittest.main()
