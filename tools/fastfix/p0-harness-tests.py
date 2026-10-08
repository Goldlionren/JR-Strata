"""CPU-only controller gates, using fake service/process/resource observations."""
import ast,json,re,subprocess,sys,tempfile,types,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[2]
source=(R/'tools/fastfix/p0-maintenance.py').read_text()
def function(name, ns):
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<controller gate>','exec'),ns)
    return ns[name]
class Gates(unittest.TestCase):
    def test_admission_reserves_cleanup_and_restoration(self):
        ns={'time':types.SimpleNamespace(monotonic=lambda:0),'deadline':2700}
        f=function('admission',ns)
        f(1680)
        with self.assertRaises(RuntimeError):f(1681)
    def test_dry_run_no_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'must-not-exist'
            p=subprocess.run([sys.executable,'-B',str(R/'tools/fastfix/p0-maintenance.py'),'--out',str(out)],capture_output=True,text=True,check=True)
            plan=json.loads(p.stdout);self.assertEqual(plan['max_minutes'],45)
            self.assertEqual(plan['cleanup_minutes'],35);self.assertEqual(len(plan['tests']),8)
            self.assertFalse(out.exists())
    def stop(self, journal='', engine='', owners=(), listener='', rc=0):
        with tempfile.TemporaryDirectory() as tmp:
            e=Path(tmp);(e/'mtp-on-engine.log').write_text(engine);calls=[]
            def cmd(*args,**kw):
                calls.append(args)
                return types.SimpleNamespace(stdout=journal if args[0]=='journalctl' else listener if args[0]=='ss' else '',stderr='',returncode=rc if args[0]=='systemctl' else 0)
            ns={'exp_started':True,'E':e,'cmd':cmd,'save':lambda n,d:(e/n).write_text(d),'start':1,'re':re,
                'UNIT':'test-only.service','NAME':'test-only-container','containers':lambda:list(owners),'free_check':lambda:calls.append(('healthy-and-free',))}
            function('stop_exp',ns)()
            self.assertIn(('healthy-and-free',),calls)
            self.assertFalse(ns['exp_started'])
    def test_clean_teardown(self):self.stop()
    def test_unsafe_queue_exit_blocks_restore(self):
        with self.assertRaises(RuntimeError):self.stop(engine='FASTFIX_UNSAFE_TEARDOWN')
    def test_timeout_protocol_blocks_restore(self):
        with self.assertRaises(RuntimeError):self.stop(journal='expert readiness device wait expired')
    def test_surviving_engine_blocks_restore(self):
        with self.assertRaises(RuntimeError):self.stop(owners=['test-only-container'])
    def test_surviving_listener_blocks_restore(self):
        with self.assertRaises(RuntimeError):self.stop(listener='LISTEN')
    def test_systemd_stop_error_blocks_restore(self):
        with self.assertRaises(RuntimeError):self.stop(rc=1)
    def test_no_reuse_of_old_artifact_or_window(self):
        self.assertNotIn('resume-start',source)
        self.assertIn("D/'p0-frozen.json'",source)
        self.assertIn("stopped=True # restore even if the stop command itself times out",source)
        self.assertNotIn("spec=0)",source)
        self.assertIn("slots=10831",source)
    def test_archived_budget_and_invalid_loaded_profiles(self):
        metrics=json.loads((R/'logs/fastfix/window-01-resume/historical-metrics-start.json').read_text())
        log='13745 of 13745 experts missing from VRAM mirrored'
        f=function('validate_loaded_profile',{'re':re})
        self.assertEqual(f(metrics,log),10831)
        for key,value in [('expert_slots',10832),('expert_cache_mib',17991),('vram_free_mib',511),('mtp_max',3),('kv_resident',16384)]:
            changed=json.loads(json.dumps(metrics));changed['engine'][key]=value
            with self.assertRaises(RuntimeError):f(changed,log)
        with self.assertRaises(RuntimeError):f(metrics,'13744 of 13745 experts missing from VRAM mirrored')
if __name__=='__main__':unittest.main()
