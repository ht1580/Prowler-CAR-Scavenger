"""Explicit, narrow deviations needed for real standing/crouch holding states.

Original sequence IDs, activities, events and the 124-descriptor prefix remain
stable. Two crouch offsets, seven drum phase keys, one phase sequence and two
client-controlled pose parameters append; gameplay activities are untouched.
"""
CROUCH_ANIMS=('crouch_offset_anim','crouch_offset_ads_anim')
DRUM_ANIMS=tuple(f'prowler_drum_index_{i}' for i in range(7))
EXTRA_ANIMS=CROUCH_ANIMS+DRUM_ANIMS
POSE_PARAMETER='prowler_crouch'
DRUM_PARAMETER='prowler_drum'
POSE_PARAMETERS=[POSE_PARAMETER,DRUM_PARAMETER]

def is_hold(name):return name.startswith('idle_seq') and name!='idle_seq_autoplay'

def expected_sequences(stock,world=False):
 result=[]
 for old in stock.sequences():
  item=dict(old)
  if not world and item['name']=='idle_seq_autoplay':
   item['blend']=[2,2]
   item['raw']=old['raw']+[len(stock.anims()),len(stock.anims())+1]
   item['anims']=old['anims']+list(CROUCH_ANIMS)
  result.append(item)
 if not world:
  indices=list(range(len(stock.anims())+2,len(stock.anims())+9))
  result.append(dict(name='prowler_drum_autoplay',activity='',blend=[7,1],raw=indices,anims=list(DRUM_ANIMS),looping=True,delta=True,autoplay=True))
 return result

def expected_flags(name,stock_flags,world=False):
 return stock_flags

def validate(stock,built,world=False):
 expected=stock.anims()+(list(EXTRA_ANIMS) if not world else [])
 assert built.anims()==expected,'original descriptor prefix or explicit crouch append differs'
 assert built.sequences()==expected_sequences(stock,world),'sequence IDs, activities or allowed hold references differ'
 assert built.poseparams()==stock.poseparams()+(POSE_PARAMETERS if not world else [])
 for (sr,sn),(br,bn) in zip(stock.table(192,232,4),built.table(192,232,4)):
  assert sn==bn
  assert built.i(br+12)==expected_flags(sn,stock.i(sr+12),world),(sn,'sequence flags')
 return True
