"""Fit the native low sprint cycle to Titanfall's fixed first-person eye."""
from mathutils import Vector
from core import matrix,lerp

def low_transform(gun,first):
 # Native normal sprint travels24units fore/aft and passes behind the TF2
 # eye. Keep its phase and changing direction with a smaller rigid excursion.
 position=first.translation+(gun.translation-first.translation)*.20+Vector((0,-6,0))
 rotation=first.to_quaternion().slerp(gun.to_quaternion(),.25)
 return matrix(position,rotation)@gun.inverted()

def meet_cycle(target,running,weight):
 # Blend each native limb/prop relative to the aligned gun at the sprint end.
 # The other end stays the original hidden equip or two-handed held pose.
 gun=target['def_c_base'];inverse=gun.inverted();runinverse=running['def_c_base'].inverted()
 return {n:gun@lerp(inverse@M,runinverse@running[n],weight) if n in running else M.copy() for n,M in target.items()}
