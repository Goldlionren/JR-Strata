import ast,json,pathlib,socket,unittest
import start as S
R=pathlib.Path(__file__).resolve().parents[2];D=R/'deploy/fastfix'
class Deployment(unittest.TestCase):
    def test_port_reuse_rejects_actual_listener(self):
        with socket.socket() as server:
            server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            server.bind(('127.0.0.1',0));server.listen();port=server.getsockname()[1]
            with self.assertRaises(OSError):S.check_port(port)
    def test_port_reuse_allows_completed_connection(self):
        server=socket.socket();server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        server.bind(('127.0.0.1',0));server.listen();port=server.getsockname()[1]
        client=socket.create_connection(('127.0.0.1',port));accepted,_=server.accept()
        accepted.close();self.assertEqual(client.recv(1),b'');client.close();server.close()
        S.check_port(port)
    def test_inference_args_identical(self):
        a=json.loads((R/'tools/fastfix/mirror-repair-runtime.json').read_text());b=json.loads((D/'runtime.json').read_text())
        self.assertEqual(a['args'],b['args'])
        for k in a.keys()-{'exe','host','port','log'}:self.assertEqual(a[k],b[k])
        self.assertEqual((b['host'],b['port']),('127.0.0.1',18083))
    def test_native_server_unchanged_path_and_lifecycle(self):
        s=(D/'start.py').read_text();u=(D/'jr-strata-sycl-fastfix.service').read_text()
        self.assertIn('sycl/serve/server_intel.py',s);self.assertIn('os.execve',s)
        for v in ['KillMode=process','KillSignal=SIGTERM','SendSIGKILL=no','TimeoutStopSec=180']:self.assertIn(v,u)
        self.assertNotIn('ExecStop=',u)
    def test_mutual_exclusion_and_bounded_restart(self):
        s=(D/'jr-strata-sycl-fastfix.service').read_text()
        for v in ['Conflicts=jr-strata-sycl-rc1.service','After=jr-strata-sycl-rc1.service','StartLimitBurst=3','RestartPreventExitStatus=78 86','WantedBy=default.target']:self.assertIn(v,s)
    def test_unchanged_docker_flags_and_guards(self):
        s=(D/'engine-wrapper.py').read_text()
        for v in ['STRATA_ARENA_ALIAS_CHECK=1','STRATA_HOST_UNCACHED=1','STRATA_VERIFY_DEVICE_PLAN=1','STRATA_APLAN_DIAG=1','S.prior_incident_guard','S.health','S.SHA']:self.assertIn(v,s)
        self.assertNotIn('STRATA_VERIFY_NO_HOST=1',s);self.assertNotIn('STRATA_TEST_VERIFY_NO_DRAFT=1',s)
    def test_no_rc1_fallback_or_force_kill(self):
        for name in ['start.py','engine-wrapper.py','ready.py']:
            s=(D/name).read_text();ast.parse(s)
            self.assertNotIn('pkill',s);self.assertNotIn('SIGKILL',s)
            self.assertNotIn("'start','jr-strata-sycl-rc1.service'",s)
    def test_resource_checkpoints_separate(self):
        self.assertIn('22*1024**3',(D/'start.py').read_text())
        self.assertIn('32*1024**2',(D/'start.py').read_text())
        self.assertIn("e['vram_free_mib']<512",(D/'ready.py').read_text())
if __name__=='__main__':unittest.main()
