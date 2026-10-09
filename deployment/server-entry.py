#!/usr/bin/env python3
"""Run original frontend; select only Monitor's PCI device. No engine/UI rewrite."""
import glob,json,sys
from pathlib import Path
R=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(R/'app'),str(R/'app/sycl/serve')]
import server_intel as I
import xe_telemetry as X
pci=json.loads((R/'deployment/settings.json').read_text())['gpu_pci']
class Selected(X._XeGpu):
 def __init__(self,index=0):
  # Inference uses only this card's DRM nodes. Avoid attributing another GPU's samples.
  self.dev=str(Path('/sys/bus/pci/devices')/pci);self.hwmon=None;self._e=None
  for n in glob.glob(self.dev+'/hwmon/hwmon*/name'):self.hwmon=str(Path(n).parent)
 def _stat(self):
  # The historical global root sampler lacks a portable PCI identity; do not trust it.
  return None
I.T.gpu_reader=lambda index=0,amd=False:Selected(index)
I.install_switcher(sys.argv[1:]);I.install_logprobs()
raise SystemExit(I.S.main())
