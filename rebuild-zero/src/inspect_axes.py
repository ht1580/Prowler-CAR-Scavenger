import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import *
o,p,fs,_=smd(STOCK/'view/v_car101.smd');g=globals_(o,p,fs[0])
for n in ('jx_c_delta','def_c_base','def_l_wrist'):
 print('STOCK',n,list(g[n].translation),list(g[n].to_quaternion()))
for path in (STOCK/'view/ptpov_car101_anims/draw_seq.smd',):
 o,p,fs,_=smd(path);g=globals_(o,p,fs[-1]);print('STOCKHOLD',list(g['def_c_base'].translation),list(g['def_l_wrist'].translation))
c=Clip(SOURCE/'apex_animations/animrig/techart/mshop/weapons/class/smg/prowler/anims_prowler_base_v_animRig/draw_0.cast');g=globals_(c.order,c.parent,c.sample(c.end));print('NATIVEHOLD',list(g['def_c_base'].translation),list(g['def_l_wrist'].translation),list(g['jx_c_delta'].to_quaternion()))
