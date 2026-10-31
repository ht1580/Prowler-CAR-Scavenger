"""Match sprint transition ends while preserving the complete native loop."""
from core import lerp

def meet_cycle(target,running,weight,parent):
 # Blend each native limb/prop relative to the aligned gun at the sprint end.
 # The other end stays the original hidden equip or two-handed held pose.
 gun=target['def_c_base'];inverse=gun.inverted();runinverse=running['def_c_base'].inverted()
 def affected(n):
  if n.startswith(('def_l_','def_r_','ja_l_','ja_r_')):return True
  while n:
   if n=='ja_c_propGun':return True
   n=parent.get(n)
  return False
 return {n:gun@lerp(inverse@M,runinverse@running[n],weight) if n in running and affected(n) else M.copy() for n,M in target.items()}
