import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def find_diffs(a, b, chunk=4096):
    positions = []
    for start in range(0, len(a), chunk):
        end = min(start + chunk, len(a))
        if a[start:end] != b[start:end]:
            positions.extend(i for i in range(start, end) if a[i] != b[i])
    return positions


def merge_positions(positions, gap=8):
    if not positions:
        return []
    ranges = []
    start = prev = positions[0]
    for pos in positions[1:]:
        if pos - prev <= gap:
            prev = pos
            continue
        ranges.append((start, prev + 1))
        start = prev = pos
    ranges.append((start, prev + 1))
    return ranges


def cmd_diff(args):
    orig = Path(args.original).read_bytes()
    patched = Path(args.patched).read_bytes()
    if len(orig) != len(patched):
        print("Original and patched files must be the same size")
        sys.exit(1)

    positions = find_diffs(orig, patched)
    if not positions:
        print("No differences found")
        sys.exit(1)

    ops = []
    for i1, i2 in merge_positions(positions, args.merge_gap):
        ops.append({
            "i1": i1,
            "i2": i2,
            "orig_hex": orig[i1:i2].hex(),
            "new_hex": patched[i1:i2].hex(),
        })

    patches_dir = Path(args.patches_dir)
    patches_dir.mkdir(parents=True, exist_ok=True)
    name = args.name or Path(args.original).stem
    out_path = patches_dir / f"{name}.json"
    out_path.write_text(json.dumps({
        "name": name,
        "orig_sha256": sha256(orig),
        "ops": ops,
    }, indent=2))
    print(f"Saved {out_path} ({len(ops)} op(s))")


def cmd_apply(args):
    in_path = Path(args.input)
    data = in_path.read_bytes()
    digest = sha256(data)

    patches_dir = Path(args.patches_dir)
    defs = [json.loads(p.read_text()) for p in sorted(patches_dir.glob("*.json"))]

    match = next((d for d in defs if d["orig_sha256"] == digest), None)
    if match is None:
        print(f"No patch matches this file (sha256={digest})")
        for d in defs:
            print(f"  {d['name']}: {d['orig_sha256']}")
        sys.exit(1)

    print(f"Matched patch '{match['name']}' ({len(match['ops'])} op(s))")

    out = bytearray(data)
    for op in match["ops"]:
        i1, i2 = op["i1"], op["i2"]
        expected = bytes.fromhex(op["orig_hex"])
        if bytes(out[i1:i2]) != expected:
            print(f"Mismatch at offset {i1}-{i2}, refusing to patch")
            sys.exit(1)
        out[i1:i2] = bytes.fromhex(op["new_hex"])

    out_path = Path(args.out) if args.out else in_path.with_name(in_path.stem + "_patched" + in_path.suffix)
    out_path.write_bytes(out)
    print(f"Wrote {out_path}")


def cmd_list(args):
    patches_dir = Path(args.patches_dir)
    for p in sorted(patches_dir.glob("*.json")):
        d = json.loads(p.read_text())
        print(f"{d['name']:20s} sha256={d['orig_sha256']} ops={len(d['ops'])}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_diff = sub.add_parser("diff")
    p_diff.add_argument("original")
    p_diff.add_argument("patched")
    p_diff.add_argument("--name")
    p_diff.add_argument("--patches-dir", default="patches")
    p_diff.add_argument("--merge-gap", type=int, default=8)
    p_diff.set_defaults(func=cmd_diff)

    p_apply = sub.add_parser("apply")
    p_apply.add_argument("input")
    p_apply.add_argument("--patches-dir", default="patches")
    p_apply.add_argument("--out")
    p_apply.set_defaults(func=cmd_apply)

    p_list = sub.add_parser("list")
    p_list.add_argument("--patches-dir", default="patches")
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
