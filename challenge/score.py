"""Unblinding: checks the sealed answers' hash, then scores decisions.json.

    python score.py
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SEALED_SHA256 = "befa3476a81eea982a74f8e8b5a061eab2c20adceefedba91752ceac33bc1e51"

raw = open(os.path.join(HERE, "sealed", "answers.json"), "rb").read()
assert hashlib.sha256(raw).hexdigest() == SEALED_SHA256, "sealed answers were modified"
truth = {p["id"]: p for p in json.loads(raw)}
dec = json.load(open(os.path.join(HERE, "decisions.json")))

rows, score = [], {"pci": 0, "rate": 0}
for pid, d in dec["blind"].items():
    t = truth[pid]
    want = "conscious-like" if t["state"] == "wake" else "unconscious-like"
    ok_p, ok_r = d["label_by_pci"] == want, d["label_by_rate"] == want
    score["pci"] += ok_p; score["rate"] += ok_r
    rows.append(dict(id=pid, true_state=t["state"], hidden_drive=t["nu_ext"], pci=d["pci"],
                     rate_hz=d["rate_hz"], pci_correct=ok_p, rate_correct=ok_r))

n = len(rows)
wake = [r["pci"] for r in rows if r["true_state"] == "wake"]
sleep = [r["pci"] for r in rows if r["true_state"] == "sleep"]
summary = dict(n=n, pci_correct=score["pci"], rate_correct=score["rate"],
               P1_pci_at_least_14=score["pci"] >= 14,
               P2_rate_worse_than_pci=score["rate"] < score["pci"],
               P3_perfect_pci_separation=min(wake) > max(sleep),
               cutoffs=dec["cutoffs"])
json.dump(dict(summary=summary, patients=rows), open(os.path.join(HERE, "results.json"), "w"), indent=1)
for r in sorted(rows, key=lambda r: r["pci"]):
    print(f"{r['id']}  {r['true_state']:5s}  drive {r['hidden_drive']:.3f}  PCI {r['pci']:.3f} "
          f"{'ok ' if r['pci_correct'] else 'MISS'}  rate {r['rate_hz']:.2f} {'ok' if r['rate_correct'] else 'MISS'}")
print(json.dumps(summary, indent=1))
