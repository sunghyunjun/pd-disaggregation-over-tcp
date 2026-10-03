#!/usr/bin/env python3
"""Delete blobs in ~/.cache/huggingface/hub/blobs that no model snapshot references (new hf CLI stores
all blobs in one shared dir; deleting a partial model dir leaves its blobs behind). Lesson from round A'."""
import os, glob
hub=os.path.expanduser("~/.cache/huggingface/hub"); blobs=os.path.join(hub,"blobs")
ref={os.path.realpath(l) for l in glob.glob(os.path.join(hub,"models--*","snapshots","*","**"), recursive=True) if os.path.islink(l)}
ref|={os.path.realpath(l) for l in glob.glob(os.path.join(hub,"datasets--*","snapshots","*","**"), recursive=True) if os.path.islink(l)}
total=freed=n=0
for root,_,files in os.walk(blobs):
    for f in files:
        p=os.path.join(root,f); s=os.path.getsize(p); total+=s
        if os.path.realpath(p) not in ref: os.remove(p); freed+=s; n+=1
print(f"blobs {total/1e9:.1f} GB, referenced {len(ref)}, deleted {n} files / {freed/1e9:.1f} GB")
