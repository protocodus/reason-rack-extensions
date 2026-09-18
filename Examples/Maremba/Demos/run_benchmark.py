#!/usr/bin/env python3
"""
Maremba Physical Modeling DSP Benchmark & Demo Song Generator
cz.protocodus.Maremba (Protocodus)

Automates downloading public domain classical piano MIDIs, converts them to
timed note event streams, executes the high-performance C++ physical-modeled
synthesis engine, renders CD-quality 44.1 kHz stereo WAV files for all 3 models,
and outputs high-resolution DSP benchmark performance metrics.
"""

import os
import sys
import glob
import json
import struct
import argparse
import subprocess
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
MIDI_DIR = BASE_DIR / "Midi"
EVENTS_DIR = BASE_DIR / "Events"
AUDIO_DIR = BASE_DIR / "Audio"
RENDERER_BIN = BASE_DIR / "maremba_renderer"

SONGS = {
    "01_Bach_Prelude_C_Major": {
        "title": "J.S. Bach - Prelude in C Major, BWV 846",
        "url": "https://raw.githubusercontent.com/reality3d/3d-piano-player/master/midi/bach_846.mid",
        "filename": "01_Bach_Prelude_C_Major.mid"
    },
    "02_Beethoven_Fur_Elise": {
        "title": "L. v. Beethoven - Für Elise (Poco moto)",
        "url": "https://raw.githubusercontent.com/reality3d/3d-piano-player/master/midi/for_elise_by_beethoven.mid",
        "filename": "02_Beethoven_Fur_Elise.mid"
    },
    "03_Joplin_The_Entertainer": {
        "title": "Scott Joplin - The Entertainer (Ragtime Two-Step)",
        "url": "https://raw.githubusercontent.com/ioccc-src/winner/master/2020/otterness/entertainer.mid",
        "filename": "03_Joplin_The_Entertainer.mid"
    },
    "04_Beethoven_Moonlight_Sonata": {
        "title": "L. v. Beethoven - Moonlight Sonata (Adagio sostenuto)",
        "url": "https://raw.githubusercontent.com/reality3d/3d-piano-player/master/midi/mond_1.mid",
        "filename": "04_Beethoven_Moonlight_Sonata.mid"
    },
    "05_Mozart_Sonata_Facile": {
        "title": "W.A. Mozart - Piano Sonata No. 16 in C Major, K. 545",
        "url": "https://raw.githubusercontent.com/reality3d/3d-piano-player/master/midi/mz_545_1.mid",
        "filename": "05_Mozart_Sonata_Facile.mid"
    }
}

MODELS = [
    {"id": 0, "code": "Rosewood", "name": "Imperial Rosewood 5.0 (Concert Grand)", "default_mallet": 0},
    {"id": 1, "code": "Padauk",   "name": "Mayan Padauk 4.3 (Artisan Wood Bark)", "default_mallet": 1},
    {"id": 2, "code": "Balafon",  "name": "Balafon Ancestral (Calabash & Mirliton Buzz)", "default_mallet": 2},
    {"id": 3, "code": "Kalimba",  "name": "Kalimba Artisan 17-Key (African Thumb Piano)", "default_mallet": 1}
]

STRIKER_COMPARISONS = [
    {
        "song_key": "01_Bach_Prelude_C_Major",
        "model_id": 0,
        "model_code": "Rosewood",
        "mallets": [
            (0, "SoftYarn", "Soft Wool Yarn"),
            (1, "MediumCord", "Medium Concert Cord"),
            (2, "HardRubber", "Hard Rubber"),
            (3, "WoodBaton", "Wood Baton")
        ]
    },
    {
        "song_key": "04_Beethoven_Moonlight_Sonata",
        "model_id": 3,
        "model_code": "Kalimba",
        "mallets": [
            (0, "ThumbFlesh", "Thumb Flesh Pad"),
            (1, "NaturalThumb", "Natural Thumb"),
            (2, "ThumbnailSnap", "Thumbnail Snap"),
            (3, "ThumbPick", "Thumb Pick")
        ]
    }
]


def ensure_midi_files():
    MIDI_DIR.mkdir(parents=True, exist_ok=True)
    for key, info in SONGS.items():
        dest = MIDI_DIR / info["filename"]
        if not dest.exists():
            print(f"[*] Downloading {info['filename']} from public domain repository...")
            try:
                req = urllib.request.Request(info["url"], headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    dest.write_bytes(resp.read())
                print(f"    Saved {info['filename']} ({dest.stat().st_size} bytes)")
            except Exception as e:
                print(f"    [!] Failed to download {info['filename']}: {e}")
                sys.exit(1)


def parse_smf(midi_bytes):
    """Pure Python Standard MIDI File (SMF Type 0/1) to timed note events."""
    magic, hdr_len, fmt, ntrks, division = struct.unpack(">4sIHHH", midi_bytes[:14])
    pos = 14
    all_events = []

    for trk_idx in range(ntrks):
        if pos >= len(midi_bytes):
            break
        trk_magic, trk_len = struct.unpack(">4sI", midi_bytes[pos:pos+8])
        pos += 8
        trk_data = midi_bytes[pos:pos+trk_len]
        pos += trk_len

        ptr, cur_tick, last_status = 0, 0, 0
        while ptr < len(trk_data):
            delta = 0
            while True:
                b = trk_data[ptr]
                ptr += 1
                delta = (delta << 7) | (b & 0x7F)
                if not (b & 0x80):
                    break
            cur_tick += delta
            if ptr >= len(trk_data):
                break
            b = trk_data[ptr]
            if b & 0x80:
                status = b
                ptr += 1
            else:
                status = last_status
            last_status = status

            ev_type = status & 0xF0
            if status == 0xFF:  # Meta
                mtype = trk_data[ptr]
                ptr += 1
                mlen = 0
                while True:
                    b = trk_data[ptr]
                    ptr += 1
                    mlen = (mlen << 7) | (b & 0x7F)
                    if not (b & 0x80):
                        break
                mdata = trk_data[ptr:ptr+mlen]
                ptr += mlen
                if mtype == 0x51 and len(mdata) >= 3:
                    tempo_us = int.from_bytes(mdata[:3], "big")
                    all_events.append((cur_tick, "tempo", tempo_us, 0))
            elif status in (0xF0, 0xF7):
                while ptr < len(trk_data) and trk_data[ptr] != 0xF7:
                    ptr += 1
                ptr += 1
            elif ev_type in (0x80, 0x90):
                note = trk_data[ptr]
                vel = trk_data[ptr+1]
                ptr += 2
                if ev_type == 0x80 or vel == 0:
                    all_events.append((cur_tick, "note_off", note, 0))
                else:
                    all_events.append((cur_tick, "note_on", note, vel))
            elif ev_type in (0xA0, 0xB0, 0xE0):
                ptr += 2
            elif ev_type in (0xC0, 0xD0):
                ptr += 1

    all_events.sort(key=lambda x: x[0])
    cur_time, last_tick, cur_tempo = 0.0, 0, 500000
    timed_events = []

    for tick, etype, p1, p2 in all_events:
        dtick = tick - last_tick
        cur_time += (dtick / division) * (cur_tempo / 1000000.0)
        last_tick = tick
        if etype == "tempo":
            cur_tempo = p1
        elif etype == "note_on":
            timed_events.append((cur_time, 1, p1, p2))
        elif etype == "note_off":
            timed_events.append((cur_time, 0, p1, 0))

    return timed_events


def convert_midi_to_events():
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    for key, info in SONGS.items():
        midi_path = MIDI_DIR / info["filename"]
        events_path = EVENTS_DIR / f"{key}.events"
        data = midi_path.read_bytes()
        events = parse_smf(data)
        with open(events_path, "w") as f:
            f.write(f"# Maremba Event Stream: {info['title']}\n")
            f.write(f"# Format: time_sec event_type(1:on,0:off) note velocity\n")
            for t, etype, note, vel in events:
                f.write(f"{t:.4f} {etype} {note} {vel}\n")
        note_ons = sum(1 for e in events if e[1] == 1)
        total_dur = events[-1][0] if events else 0.0
        print(f"[*] Prepared {key}.events: {note_ons} notes, {total_dur:.1f}s duration")


def compile_renderer():
    deps = [
        BASE_DIR / "maremba_renderer.cpp",
        PROJECT_DIR / "DSP" / "MarembaVoice.cpp",
        PROJECT_DIR / "DSP" / "MarembaEngine.cpp",
        PROJECT_DIR / "DSP" / "MarembaVoice.h",
        PROJECT_DIR / "DSP" / "MarembaEngine.h",
    ]
    max_dep_mtime = max(p.stat().st_mtime for p in deps if p.exists())
    if not RENDERER_BIN.exists() or RENDERER_BIN.stat().st_mtime < max_dep_mtime:
        print("[*] Compiling high-performance C++ demo renderer (clang++ -O3)...")
        cmd = [
            "clang++", "-std=c++17", "-O3",
            "-I", str(PROJECT_DIR),
            str(PROJECT_DIR / "DSP" / "MarembaVoice.cpp"),
            str(PROJECT_DIR / "DSP" / "MarembaEngine.cpp"),
            str(BASE_DIR / "maremba_renderer.cpp"),
            "-o", str(RENDERER_BIN)
        ]
        res = subprocess.run(cmd, cwd=str(PROJECT_DIR))
        if res.returncode != 0:
            print("[!] Compilation failed!")
            sys.exit(1)
        print("[*] Compiled maremba_renderer successfully!")


def generate_player_html(results):
    html_path = BASE_DIR / "demo_player.html"
    
    def render_table(items):
        rows = ""
        for r in items:
            wav_rel = f"Audio/{os.path.basename(r['output_file'])}"
            striker_badge = f'<span class="badge striker-{r.get("striker_id", 0)}">{r.get("striker", "Default")}</span>'
            rows += f"""
            <tr>
                <td style="font-weight:600; color:#f0f0f0;">{r['song_title']}</td>
                <td><span class="badge model-{r['model_id']}">{r['model']}</span></td>
                <td>{striker_badge}</td>
                <td><code>{r['real_time_factor']:.1f}x</code></td>
                <td>{r['audio_duration_sec']:.1f}s</td>
                <td>{r['render_time_ms']:.1f} ms</td>
                <td>{r['peak_db']:.1f} dBFS</td>
                <td>
                    <audio controls preload="none" style="height:32px; width:220px;">
                        <source src="{wav_rel}" type="audio/wav">
                    </audio>
                </td>
            </tr>
            """
        return rows

    showcase_items = [r for r in results if r.get("category") == "Showcase"]
    study_items = [r for r in results if r.get("category") == "Striker Study"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Maremba Physical Modeling Showcase & Benchmark</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 30px; background: #131518; color: #d8dcde; }}
        h1 {{ color: #e6b350; font-size: 26px; margin-bottom: 4px; letter-spacing: 0.5px; }}
        h2 {{ color: #9aa0a6; font-size: 13px; font-weight: normal; margin-top: 0; margin-bottom: 24px; }}
        h3 {{ color: #e0bb6b; font-size: 16px; margin-top: 36px; margin-bottom: 12px; border-bottom: 1px solid #2d333b; padding-bottom: 6px; text-transform: uppercase; letter-spacing: 1px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 8px; background: #1c1f24; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.5); }}
        th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #282c34; font-size: 13px; }}
        th {{ background: #22262c; color: #d0a040; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; }}
        tr:hover {{ background: #262a32; }}
        code {{ background: #101214; padding: 2px 6px; border-radius: 4px; color: #50e090; font-family: "SFMono-Regular", Menlo, Monaco, monospace; font-size: 12px; }}
        .badge {{ padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; display: inline-block; }}
        .model-0 {{ background: #4a2810; color: #f0c080; border: 1px solid #7c441c; }}
        .model-1 {{ background: #5c2010; color: #ff9060; border: 1px solid #9c3c1e; }}
        .model-2 {{ background: #242c16; color: #b8e060; border: 1px solid #4a5c28; }}
        .model-3 {{ background: #3d2a10; color: #ffd070; border: 1px solid #7c541c; }}
        .striker-0 {{ background: #202b38; color: #8ec5fc; border: 1px solid #355070; }}
        .striker-1 {{ background: #22382e; color: #8ee0b8; border: 1px solid #357050; }}
        .striker-2 {{ background: #3c2a18; color: #f5b060; border: 1px solid #754a20; }}
        .striker-3 {{ background: #3c1a20; color: #f57080; border: 1px solid #752535; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 25px; }}
        .stat-card {{ background: #1c1f24; padding: 16px; border-radius: 6px; border-left: 4px solid #d0a040; box-shadow: 0 2px 8px rgba(0,0,0,0.3); }}
        .stat-num {{ font-size: 24px; font-weight: bold; color: #fff; margin-top: 4px; }}
        .stat-label {{ font-size: 11px; text-transform: uppercase; color: #888; }}
    </style>
</head>
<body>
    <h1>Maremba: 100% Physical-Modeled Acoustic Marimba & Kalimba</h1>
    <h2>cz.protocodus.Maremba · Zero Samples · 5-Mode Resonator with Quarter-Wave Coupling, Mirliton Buzz & Cantilever Tines</h2>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">Total Tracks Rendered</div>
            <div class="stat-num">{len(results)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Average Real-Time Speedup</div>
            <div class="stat-num">{sum(r['real_time_factor'] for r in results)/len(results):.1f}x</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Total Audio Generated</div>
            <div class="stat-num">{sum(r['audio_duration_sec'] for r in results):.0f}s</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Total Compute Runtime</div>
            <div class="stat-num">{sum(r['render_time_ms'] for r in results)/1000.0:.2f}s</div>
        </div>
    </div>

    <h3>Acoustic Model Showcase (5 Masterworks x 4 Instruments)</h3>
    <table>
        <thead>
            <tr>
                <th>Composition</th>
                <th>Instrument Model</th>
                <th>Striker Articulation</th>
                <th>DSP Speedup</th>
                <th>Audio Length</th>
                <th>Compute Time</th>
                <th>Peak Level</th>
                <th>Audition Track</th>
            </tr>
        </thead>
        <tbody>
            {render_table(showcase_items)}
        </tbody>
    </table>

    <h3>Striker & Mallet Articulation Study (Timbre & Transient Hardness Sweep)</h3>
    <table>
        <thead>
            <tr>
                <th>Composition</th>
                <th>Instrument Model</th>
                <th>Striker Articulation</th>
                <th>DSP Speedup</th>
                <th>Audio Length</th>
                <th>Compute Time</th>
                <th>Peak Level</th>
                <th>Audition Track</th>
            </tr>
        </thead>
        <tbody>
            {render_table(study_items)}
        </tbody>
    </table>
</body>
</html>
"""
    html_path.write_text(html)
    print(f"[*] Generated interactive HTML audition player: {html_path}")


def main():
    parser = argparse.ArgumentParser(description="Maremba Physical Modeling DSP Benchmark")
    parser.add_argument("--duration", type=float, default=45.0, help="Maximum audio duration per demo track in seconds (default: 45.0)")
    parser.add_argument("--full", action="store_true", help="Render complete compositions without truncation")
    parser.add_argument("--oversampling", type=int, choices=[0, 1, 2], default=0, help="0: 2x Studio (default), 1: 4x High-Res, 2: 8x Archival")
    args = parser.parse_args()

    max_dur = 99999.0 if args.full else args.duration

    print("=================================================================")
    print("      MAREMBA PHYSICAL MODELING BENCHMARK & DEMO GENERATOR      ")
    print("=================================================================")

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    ensure_midi_files()
    convert_midi_to_events()
    compile_renderer()

    results = []

    print("\n[*] Commencing synthesis and benchmark execution...\n")
    print(f"{'SONG':<30} | {'MODEL':<24} | {'STRIKER':<18} | {'AUDIO (s)':<9} | {'RENDER (ms)':<11} | {'SPEEDUP':<10} | {'PEAK (dBFS)':<11}")
    print("-" * 125)

    # 1. Instrument Model Showcase (5 songs x 4 models with optimal default strikers)
    for song_key, song_info in SONGS.items():
        events_file = EVENTS_DIR / f"{song_key}.events"

        for model_info in MODELS:
            mid = model_info["id"]
            mcode = model_info["code"]
            def_mallet = model_info.get("default_mallet", 1)
            out_wav = AUDIO_DIR / f"{song_key}_{mcode}.wav"

            cmd = [
                str(RENDERER_BIN),
                "--events", str(events_file),
                "--output", str(out_wav),
                "--model", str(mid),
                "--mallet", str(def_mallet),
                "--oversampling", str(args.oversampling),
                "--max-duration", str(max_dur),
                "--json"
            ]

            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0:
                print(f"[!] Error rendering {song_key} with model {mcode}: {proc.stderr}")
                continue

            try:
                metrics = json.loads(proc.stdout)
                metrics["song_key"] = song_key
                metrics["song_title"] = song_info["title"]
                metrics["category"] = "Showcase"
                results.append(metrics)

                print(f"{song_info['title'][:30]:<30} | {model_info['name'][:24]:<24} | {metrics.get('striker', '')[:18]:<18} | {metrics['audio_duration_sec']:<9.1f} | {metrics['render_time_ms']:<11.1f} | {metrics['real_time_factor']:<9.1f}x | {metrics['peak_db']:<11.1f}")
            except Exception as e:
                print(f"[!] Failed to parse metrics: {proc.stdout}")

    # 2. Striker Articulation Study Tracks
    print("\n[*] Rendering Striker & Mallet Articulation Studies...\n")
    for comp in STRIKER_COMPARISONS:
        song_key = comp["song_key"]
        song_info = SONGS[song_key]
        events_file = EVENTS_DIR / f"{song_key}.events"
        mid = comp["model_id"]
        mcode = comp["model_code"]

        for mal_id, mal_tag, mal_name in comp["mallets"]:
            out_wav = AUDIO_DIR / f"{song_key}_{mcode}_{mal_tag}.wav"

            cmd = [
                str(RENDERER_BIN),
                "--events", str(events_file),
                "--output", str(out_wav),
                "--model", str(mid),
                "--mallet", str(mal_id),
                "--oversampling", str(args.oversampling),
                "--max-duration", str(max_dur),
                "--json"
            ]

            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0:
                print(f"[!] Error rendering {song_key} with {mal_tag}: {proc.stderr}")
                continue

            try:
                metrics = json.loads(proc.stdout)
                metrics["song_key"] = song_key
                metrics["song_title"] = f"{song_info['title']} ({mal_name})"
                metrics["category"] = "Striker Study"
                results.append(metrics)

                print(f"{metrics['song_title'][:30]:<30} | {mcode:<24} | {metrics.get('striker', '')[:18]:<18} | {metrics['audio_duration_sec']:<9.1f} | {metrics['render_time_ms']:<11.1f} | {metrics['real_time_factor']:<9.1f}x | {metrics['peak_db']:<11.1f}")
            except Exception as e:
                print(f"[!] Failed to parse metrics: {proc.stdout}")

    print("-" * 125)

    # Benchmark Summary Report
    total_audio = sum(r["audio_duration_sec"] for r in results)
    total_render_s = sum(r["render_time_ms"] for r in results) / 1000.0
    avg_speedup = total_audio / total_render_s if total_render_s > 0 else 0

    print(f"\n>>> BENCHMARK COMPLETE <<<")
    print(f"Total Tracks Rendered: {len(results)}")
    print(f"Total Audio Duration:  {total_audio:.1f} s ({total_audio/60.0:.2f} minutes)")
    print(f"Total Processing Time: {total_render_s:.2f} s")
    print(f"Aggregate DSP Speedup: {avg_speedup:.1f}x Real-Time (Faster than real-time)\n")

    generate_player_html(results)

    # Write Markdown Benchmark Report
    report_path = BASE_DIR / "BENCHMARK_REPORT.md"
    md_lines = [
        "# Maremba DSP Benchmark & Audio Verification Report",
        "",
        "**cz.protocodus.Maremba** by Protocodus · 100% Real-Time Mathematical Physical Modeling",
        "",
        "## Performance Metrics Summary",
        "",
        f"- **Total Tracks Rendered**: {len(results)} CD-Quality 44.1 kHz Stereo WAV files",
        f"- **Total Simulated Audio Duration**: {total_audio:.1f} seconds ({total_audio/60.0:.2f} minutes)",
        f"- **Total Execution Runtime**: {total_render_s:.2f} seconds",
        f"- **Aggregate Performance Speedup**: **`{avg_speedup:.1f}x` faster than real-time**",
        "",
        "## Detailed Benchmark Results Table",
        "",
        "| Composition / Test | Model | Striker | Audio Dur | Render Time | Real-Time Factor | Peak Level | Output File |",
        "|---|---|---|---|---|---|---|---|"
    ]

    for r in results:
        fname = os.path.basename(r["output_file"])
        md_lines.append(
            f"| **{r['song_title']}** | {r['model']} | {r.get('striker', 'Default')} | {r['audio_duration_sec']:.1f}s | {r['render_time_ms']:.1f}ms | `{r['real_time_factor']:.1f}x` | {r['peak_db']:.1f} dBFS | [`{fname}`](Audio/{fname}) |"
        )

    report_path.write_text("\n".join(md_lines) + "\n")
    print(f"[*] Benchmark report saved to: {report_path}")


if __name__ == "__main__":
    main()
