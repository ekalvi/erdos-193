#!/usr/bin/env python3
"""Extract searchable text from the checksum-pinned research PDFs (one core).

Resume: each whole PDF is an atomic unit. Completed outputs are SHA-256 checked
against a validated checkpoint; incompatible/corrupt state is rejected. SIGINT
and SIGTERM finish/checkpoint the current PDF, then stop. Logs/checkpoints live
under ignored .checkpoint-* paths, separate from final artifacts. No network.
Use --record-text-metadata only for an intentional catalogue/text update.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import signal
import time

import pypdf

ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = ROOT / "research/unit-step/artifacts.json"
STOP = False


def digest(data):
    return hashlib.sha256(data).hexdigest()


def packed(value):
    return json.dumps(value, sort_keys=True).encode()


def atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def repo_path(value):
    path = ROOT / value
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
        raise ValueError(f"unsafe repository path: {value}")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, default=ROOT / ".checkpoint-unit-step-pdf-text")
    parser.add_argument("--record-text-metadata", action="store_true")
    args = parser.parse_args()
    args.state_dir.mkdir(parents=True, exist_ok=True)
    log = args.state_dir / "run.jsonl"
    checkpoint = args.state_dir / "state.json"
    started = time.monotonic()

    def event(name, **fields):
        record = dict(time=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), event=name, **fields)
        line = json.dumps(record, sort_keys=True) + "\n"
        with log.open("a", encoding="utf-8") as stream:
            stream.write(line)
            stream.flush()
        print(line, end="", flush=True)

    def stop(_signum, _frame):
        global STOP
        STOP = True

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, stop)
    try:
        catalogue = json.loads(CATALOGUE.read_text())
        if catalogue["schema"] != 1 or catalogue["text_extractor"] != f"pypdf=={pypdf.__version__}":
            raise ValueError("unsupported schema or extractor version; use the catalogue-pinned pypdf")
        pdfs = catalogue["pdfs"]
        ids = [row["id"] for row in pdfs]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate catalogue IDs")
        identity = dict(schema=1, code_sha256=digest(Path(__file__).read_bytes()),
                        extractor=catalogue["text_extractor"],
                        inputs=[{k: row[k] for k in ("id", "path", "sha256", "text_path")} for row in pdfs])
        done = {}
        if checkpoint.exists():
            saved = json.loads(checkpoint.read_text())
            if saved["identity"] != identity:
                raise ValueError("incompatible checkpoint; choose a fresh --state-dir")
            done = saved["completed"]
            if saved["completed_sha256"] != digest(packed(done)) or not set(done) <= set(ids):
                raise ValueError("corrupt checkpoint")
        # Verify even completed source PDFs; never reuse text for altered input.
        for row in pdfs:
            if digest(repo_path(row["path"]).read_bytes()) != row["sha256"]:
                raise ValueError(f"source PDF checksum mismatch: {row['path']}")
        event("resume" if done else "start", identity=identity, threads=1, completed=len(done),
              total=len(pdfs), checkpoint=str(checkpoint), eta_seconds=10)
        initial = len(done)
        for row in pdfs:
            if STOP:
                event("interrupted", completed=len(done), total=len(pdfs), checkpoint=str(checkpoint))
                return 130
            output = repo_path(row["text_path"])
            if row["id"] in done:
                if not output.exists() or digest(output.read_bytes()) != done[row["id"]]["text_sha256"]:
                    raise ValueError(f"corrupt/missing completed output: {output}")
            else:
                reader = pypdf.PdfReader(repo_path(row["path"]))
                # Some embedded math fonts decode delimiters as C0 controls.
                # Mark these as unknown rather than inventing the missing glyph.
                controls = {c: "\ufffd" for c in range(32) if c not in (9, 10, 13)}
                pages = ["\n".join(line.rstrip() for line in (page.extract_text() or "").translate(controls).splitlines())
                         for page in reader.pages]
                text = f"Extracted text for search/AI. The source PDF is authoritative.\nSource: {row['path']}\n"
                text += "\n".join(f"\n=== Page {n} ===\n{page.strip()}\n" for n, page in enumerate(pages, 1))
                atomic(output, text)
                done[row["id"]] = dict(pdf_bytes=repo_path(row["path"]).stat().st_size,
                                       pdf_pages=len(pages), text_sha256=digest(output.read_bytes()))
                atomic(checkpoint, json.dumps(dict(identity=identity, completed=done,
                                                  completed_sha256=digest(packed(done))), indent=2) + "\n")
                elapsed = max(time.monotonic() - started, 1e-9)
                rate = (len(done) - initial) / elapsed
                event("progress", completed=len(done), total=len(pdfs), pdf=row["id"],
                      elapsed_seconds=elapsed, pdfs_per_second=rate,
                      eta_seconds=(len(pdfs)-len(done))/rate, checkpoint=str(checkpoint))
            if args.record_text_metadata:
                row.update(done[row["id"]])
            elif any(row.get(k) != v for k, v in done[row["id"]].items()):
                raise ValueError("catalogue text metadata differs; inspect before --record-text-metadata")
        if args.record_text_metadata:
            atomic(CATALOGUE, json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n")
        event("complete", completed=len(done), total=len(pdfs),
              elapsed_seconds=time.monotonic()-started, catalogue=str(CATALOGUE))
        return 0
    except Exception as exc:
        event("error", error=str(exc), checkpoint=str(checkpoint))
        raise


if __name__ == "__main__":
    raise SystemExit(main())
