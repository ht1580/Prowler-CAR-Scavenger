"""Verify ZIP bytes against staged assets, Northstar layout and audio contract."""
import hashlib
import io
import json
import math
import re
import struct
import sys
import wave
import zipfile
from array import array
from pathlib import Path, PurePosixPath


def verify(archive, stage):
    archive, stage = Path(archive), Path(stage)
    prefix = "Prowler.CAR.Scavenger/"
    report = {"archive": str(archive), "sha256": hashlib.sha256(archive.read_bytes()).hexdigest().upper(),
              "bytes": archive.stat().st_size, "files": [], "audio": {}, "game_tested": False}
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None, "ZIP CRC error"
        names = package.namelist()
        assert len(names) == len(set(names)), "Duplicate ZIP entry"
        expected = {prefix + path.relative_to(stage).as_posix() for path in stage.rglob("*") if path.is_file()}
        assert set(names) == expected, "ZIP and stage file lists differ"
        for name in names:
            relative = name[len(prefix):]
            assert name.startswith(prefix) and "\\" not in name and ".." not in PurePosixPath(name).parts and not name.startswith("/")
            assert PurePosixPath(relative).suffix.lower() not in (".cfg", ".dll", ".exe", ".bat", ".ps1"), name
            data = package.read(name)
            assert data == stage.joinpath(*PurePosixPath(relative).parts).read_bytes(), name
            if PurePosixPath(relative).suffix.lower() in (".json", ".txt", ".nut", ".gnut", ".md"):
                assert not data.startswith(b"\xef\xbb\xbf"), "BOM: " + name
                data.decode("utf-8")
            report["files"].append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        manifest = json.loads(package.read(prefix + "mod.json"))
        assert manifest["Name"] == "Prowler.CAR.Scavenger" and re.fullmatch(r"\d+\.\d+\.\d+", manifest["Version"])
        assert archive.name == "Prowler.CAR.Scavenger-" + manifest["Version"] + ".zip"
        assert manifest["LoadPriority"] == 0 and manifest["RequiredOnClient"] is False
        weapon = package.read(prefix + "keyvalues/scripts/weapons/mp_weapon_car.txt").decode("utf-8")
        keys = dict(re.findall(r'^\s*"([^"]+)"\s+"([^"]*)"', weapon, re.MULTILINE))
        assert {"viewmodel", "playermodel", "holstermodel"} <= set(keys)
        assert all(k in ("viewmodel", "playermodel", "holstermodel", "low_ammo_sound_name_1") or "sound" in k for k in keys), keys
        assert keys["looping_sounds"] == "1", "the Prowler full-auto sound is a loop"
        for key, mdl in (("viewmodel", "ptpov_car101"), ("playermodel", "w_car101"), ("holstermodel", "w_car101")):
            assert keys[key] == f"models/weapons/car101/{mdl}.mdl"
            model = package.read(prefix + "mod/" + keys[key])
            assert model[:4] == b"IDST" and struct.unpack_from("<I", model, 4)[0] == 53
            assert struct.unpack_from("<I", model, 80)[0] == len(model), "MDL file length mismatch"
        definitions = sorted(name for name in names if name.startswith(prefix + "audio/") and name.endswith(".json"))
        # Northstar matches EventIds case-sensitively against the lowercase Miles bank names
        bank_list = Path(__file__).resolve().parents[1] / "audio_raw/events/tf2_all_audio_events.txt"
        bank = {line.split(",", 1)[1].strip() for line in bank_list.read_text().splitlines() if "," in line}
        routed = {v for k, v in keys.items() if "sound" in k and k != "looping_sounds" and v}
        overridden = set()
        for definition_path in definitions:
            event = PurePosixPath(definition_path).stem
            definition = json.loads(package.read(definition_path))
            assert event in definition["EventId"] and definition["AudioSelectionStrategy"] in ("sequential", "random")
            assert set(definition["EventId"]) <= bank, "EventId not in the TF2 bank: " + event
            overridden |= set(definition["EventId"])
            audio = package.read(prefix + f"audio/{event}/1.wav")
            offset, chunks = 12, []
            while offset + 8 <= len(audio):
                tag, length = struct.unpack_from("<4sI", audio, offset)
                chunks.append(tag)
                offset += 8 + length + length % 2
            assert chunks == [b"fmt ", b"data"], "Unexpected WAV metadata"
            assert offset == len(audio)
            with wave.open(io.BytesIO(audio)) as sound:
                assert (sound.getnchannels(), sound.getsampwidth(), sound.getframerate()) == (2, 2, 48000)
                pcm = array("h", sound.readframes(sound.getnframes()))
                if sys.byteorder != "little":
                    pcm.byteswap()
                peak = max(abs(value) for value in pcm) / 32767
                rms = math.sqrt(sum(value * value for value in pcm) / len(pcm)) / 32767
                assert peak <= 0.9801, "Clipped audio"
                # secondshot (stock per-shot CAR crack) is deliberately silent; everything else must be audible
                assert ("secondshot" in event) == (rms == 0) and (rms == 0 or rms > 0.005), "Silent/audible mismatch: " + event
                report["audio"][event] = {"seconds": sound.getnframes() / 48000, "peak": peak, "rms": rms,
                                          "ids": definition["EventId"]}
        assert routed <= overridden, f"routed but not overridden: {routed - overridden}"
        report["version"] = manifest["Version"]
        report["file_count"] = len(names)
        report["zip_crc_ok"] = report["stage_matches_zip"] = report["text_bom_free"] = True
    # Stage is project/release/version/modname; preserve useful gate evidence in the report.
    logs = Path(__file__).resolve().parents[1] / "build/logs"
    def log_text(p):      # PowerShell 5.1 "*>" writes UTF-16LE with a BOM
        raw = p.read_bytes()
        return raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig", "replace")

    report["build_gates"] = {name: log_text(logs / name) for name in (
        "world_anim.log", "rui_fix.log", "seq_fix.log", "mdl_integrity.log", "ptpov_car101-compare.log", "w_car101-compare.log", "regressions.log", "native-view.log", "native-world.log")}
    report["status"] = "PACKAGE_OK; game validation pending"
    return report


if __name__ == "__main__":
    result = verify(sys.argv[1], sys.argv[2])
    Path(sys.argv[3]).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print("PACKAGE_VERIFY_OK", json.dumps({key: result[key] for key in ("version", "file_count", "bytes", "sha256", "game_tested")}))
