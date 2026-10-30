"""Regression for the engine's raw translation fields, independent of Crowbar pose defaults."""
import struct
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/'build/compiler_game/models/weapons/car101/ptpov_car101_conv.mdl'

def raw_positions(path, animation):
    data=Path(path).read_bytes()
    def integer(offset):return struct.unpack_from('<i',data,offset)[0]
    count,start=struct.unpack_from('<ii',data,184)
    nb,bones=struct.unpack_from('<ii',data,160)
    names=[];bind=[]
    for i in range(nb):
        r=bones+244*i; p=r+integer(r);names.append(data[p:data.index(b'\0',p)].decode())
        bind.append(struct.unpack_from('<3f',data,r+32))
    for i in range(count):
        r=start+92*i;p=r+integer(r+4)
        if data[p:data.index(b'\0',p)].decode()!=animation:continue
        # Reference ports may store offsets in an absolute descriptor consumed
        # by a DELTA sequence. Check the actual raw values in either encoding.
        p=r+integer(r+32);out={}
        for _ in range(256):
            bone,flags=data[p+4:p+6]
            if bone<len(names):
                if flags&2:values=struct.unpack_from('<3e',data,p+16)
                else:
                    scale=struct.unpack_from('<f',data,p)[0];values=[]
                    for axis in range(3):
                        offset=struct.unpack_from('<h',data,p+16+2*axis)[0]
                        value=0
                        if offset>0:
                            address=p+16+offset;valid,total=data[address:address+2]
                            assert valid>0 and total>0
                            value=struct.unpack_from('<h',data,address+2)[0]*scale
                        values.append(value+(0 if flags&1 else bind[bone][axis]))
                out[names[bone]]=values
            step=integer(p+28)
            if not step:break
            assert step>=32
            p+=step
        return out
    raise AssertionError('Animation missing: '+animation)

class RawDeltaTranslation(unittest.TestCase):
    def test_firing_does_not_add_bind_translation_to_wrists_or_rotor(self):
        # All three source channels rotate in place: the native/source SMD deltas
        # and original CAR data require zero local translation, including at rest.
        p=raw_positions(MODEL,'attack_anim')
        for bone in ('def_l_wrist','def_r_wrist','def_c_reactive_spinner_coils'):
            with self.subTest(bone=bone):
                # Explicit offset tracks use the converter's quantized RLE scale;
                # allow the same <0.01-unit bound as native mechanism verification.
                self.assertLess(max(abs(v) for v in p[bone]),.01,
                    f'{bone}: raw v53 delta translation is {p[bone]}, expected zero')
    def test_walking_does_not_double_wrist_bone_lengths(self):
        p=raw_positions(MODEL,'run_anim_static')
        for bone in ('def_l_wrist','def_r_wrist'):
            with self.subTest(bone=bone):
                self.assertLess(max(abs(v) for v in p[bone]),.01,
                    f'{bone}: walking adds raw bind position {p[bone]}')

if __name__=='__main__':unittest.main()
