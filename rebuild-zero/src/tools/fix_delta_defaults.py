"""Restore zero delta translations omitted by StudioMDL but filled with bind positions by MDLShit.

Use the v49 bone-track flags as provenance. Explicit source position tracks are never changed.
Both ordinary animation lists and sectioned lists are handled; file layout is unchanged.
"""
import argparse
import json
import struct
from pathlib import Path

def descriptors(data,version):
    header,stride=(180,100) if version==49 else (184,92)
    count,start=struct.unpack_from('<ii',data,header)
    result=[]
    for i in range(count):
        r=start+i*stride
        name=r+struct.unpack_from('<i',data,r+4)[0]
        name=data[name:data.index(b'\0',name)].decode('ascii')
        flags,frames=struct.unpack_from('<ii',data,r+12)
        ai=struct.unpack_from('<i',data,r+(56 if version==49 else 32))[0]
        si,sf=struct.unpack_from('<ii',data,r+(80 if version==49 else 52))
        starts=[]
        if not flags&0x20 and ai>0:
            if si:
                assert sf>0
                for section in range(frames//sf+2):
                    if version==49:
                        block,offset=struct.unpack_from('<ii',data,r+si+8*section)
                        assert block==0,'External animation data is unsupported'
                    else:offset=struct.unpack_from('<i',data,r+si+4*section)[0]
                    starts.append(r+offset)
            else:starts=[r+ai]
        result.append((name,flags,starts))
    return result

def tracks(data,start,version):
    result=[];p=start
    for _ in range(257):
        assert 0<=p<=len(data)-32
        bone,flags=data[p+(4 if version==53 else 0):p+(6 if version==53 else 2)]
        result.append((p,bone,flags))
        step=struct.unpack_from('<i' if version==53 else '<H',data,p+(28 if version==53 else 2))[0]
        if not step:return result
        assert step>=(32 if version==53 else 4)
        p+=step
    raise ValueError('Invalid bone-track chain')

def fix(source_path,target_path):
    source=Path(source_path).read_bytes();target=bytearray(Path(target_path).read_bytes())
    assert source[:4]==target[:4]==b'IDST'
    assert struct.unpack_from('<i',source,4)[0]==49
    assert struct.unpack_from('<i',target,4)[0]==53
    src=descriptors(source,49);dst=descriptors(target,53)
    assert len(src)==len(dst)
    edits={};checked=0
    for (name,sflags,starts),(tname,tflags,tstarts) in zip(src,dst):
        assert name==tname and bool(sflags&4)==bool(tflags&4),(name,tname)
        assert len(starts)==len(tstarts),(name,len(starts),len(tstarts))
        if not sflags&4:continue
        for s,t in zip(starts,tstarts):
            a=tracks(source,s,49);b=tracks(target,t,53)
            assert len(a)==len(b),(name,len(a),len(b))
            for (_,bone,sf),(p,tbone,tf) in zip(a,b):
                assert bone==tbone,(name,bone,tbone)
                if bone==255:continue
                assert bool(sf&16)==bool(tf&1),(name,bone,sf,tf)
                if sf&16 and not sf&(1|4):
                    assert tf&2,(name,bone,tf)
                    checked+=1
                    old=struct.unpack_from('<3e',target,p+16)
                    if any(old):edits[p+16]={'animation':name,'bone':bone,'old':old}
    for offset in edits:struct.pack_into('<3e',target,offset,0,0,0)
    Path(target_path).write_bytes(target)
    return {'checked_implicit_delta_positions':checked,'corrected_fields':len(edits),'edits':list(edits.values())}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source');parser.add_argument('target');parser.add_argument('--report')
    args=parser.parse_args();report=fix(args.source,args.target)
    if args.report:Path(args.report).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('DELTA_DEFAULTS_FIXED',report['corrected_fields'],'of',report['checked_implicit_delta_positions'])
