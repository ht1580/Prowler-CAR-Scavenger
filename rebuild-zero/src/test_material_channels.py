import unittest,json
from pathlib import Path
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[1];CFG=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'))
class MaterialChannels(unittest.TestCase):
 def test_original_colour_mask_and_coloured_illumination_channels_survive(self):
  for suffix in ('col','ilm'):
   with Image.open(Path(CFG['texture_source'])/f'prowler_v21_react_scavenger_{suffix}.png') as a, Image.open(ROOT/f'build/materials/png/scavenger_{suffix}.png') as b:
    self.assertTrue(a.convert('RGBA').tobytes()==b.convert('RGBA').tobytes(),f'{suffix}: original RGBA mask/channel content discarded')
if __name__=='__main__':unittest.main()
