"""Keep proven constant-zero offset translations exact, without RLE cancellation error."""
import json
import struct
from pathlib import Path
from fix_delta_defaults import descriptors,tracks

def fix(model_path,rig_path):
    rig_path=Path(rig_path);rig=json.loads(rig_path.read_text(encoding='utf-8'))
    model_path=Path(model_path);data=bytearray(model_path.read_bytes());edits=[]
    for name,flags,starts in descriptors(data,53):
        source=rig['animations'][name]
        if not source['delta']:continue
        # Read the authored offset values, not decoded values or bind defaults.
        zero=set(range(len(rig['order'])))
        smd=rig_path.parent/'view/anims'/source['file']
        skeleton=False
        for line in smd.read_text(encoding='ascii').splitlines():
            if line=='skeleton':skeleton=True;continue
            if not skeleton:continue
            if line=='end':break
            words=line.split()
            if not words or words[0]=='time':continue
            bone=int(words[0])
            if bone in zero and any(float(v)!=0.0 for v in words[1:4]):zero.remove(bone)
        for start in starts:
            for p,bone,bflags in tracks(data,start,53):
                if bone not in zero:continue
                if bflags&2 and data[p+16:p+22]==b'\0'*6:continue
                data[p+5]=bflags|2
                data[p+16:p+22]=b'\0'*6
                edits.append({'animation':name,'bone':rig['order'][bone]})
    model_path.write_bytes(data)
    return {'canonical_zero_translations':len(edits),'edits':edits}

if __name__=='__main__':
    import sys
    report=fix(sys.argv[1],sys.argv[2])
    print('EXACT_OFFSET_ZEROS',report['canonical_zero_translations'])
