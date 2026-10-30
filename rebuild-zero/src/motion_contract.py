"""Explicit, narrow deviations needed for real standing/crouch holding states.

Original sequence IDs, activities, events and the 124-descriptor prefix remain
stable. Two crouch-only offsets and one client-controlled pose parameter append.
Only the existing autoplay blend grid changes; gameplay activities are untouched.
"""
EXTRA_ANIMS=('crouch_offset_anim','crouch_offset_ads_anim')
POSE_PARAMETER='prowler_crouch'

def is_hold(name):return name.startswith('idle_seq') and name!='idle_seq_autoplay'

def expected_sequences(stock,world=False):
 result=[]
 for old in stock.sequences():
  item=dict(old)
  if not world and item['name']=='idle_seq_autoplay':
   item['blend']=[2,2]
   item['raw']=old['raw']+[len(stock.anims()),len(stock.anims())+1]
   item['anims']=old['anims']+list(EXTRA_ANIMS)
  result.append(item)
 return result

def expected_flags(name,stock_flags,world=False):
 return stock_flags

def validate(stock,built,world=False):
 expected=stock.anims()+(list(EXTRA_ANIMS) if not world else [])
 assert built.anims()==expected,'original descriptor prefix or explicit crouch append differs'
 assert built.sequences()==expected_sequences(stock,world),'sequence IDs, activities or allowed hold references differ'
 assert built.poseparams()==stock.poseparams()+([POSE_PARAMETER] if not world else [])
 for (sr,sn),(br,bn) in zip(stock.table(192,232,4),built.table(192,232,4)):
  assert sn==bn
  assert built.i(br+12)==expected_flags(sn,stock.i(sr+12),world),(sn,'sequence flags')
 return True
