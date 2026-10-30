"""Finishing an already-finished build must not move/shrink embedded RUI again."""
import sys,subprocess,unittest,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class FinishIdempotence(unittest.TestCase):
 def test_second_finish_produces_identical_model_bytes(self):
  files=list((ROOT/'build/compiler_game/models/weapons/car101').glob('*_conv.mdl'))
  originals={p:p.read_bytes() for p in files}
  try:
   def finish():
    r=subprocess.run([sys.executable,str(ROOT/'src/finish_models.py')],capture_output=True,text=True)
    self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
   self.assertEqual(finish(),finish(),'repeated finishing changed embedded model data')
  finally:
   for p,data in originals.items():p.write_bytes(data)

if __name__=='__main__':unittest.main()
