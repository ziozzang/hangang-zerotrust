#!/usr/bin/env python3
"""Package an explicitly qualified static artifact, never source trees or credentials."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--component',required=True,choices=['hangang','hopae','sumunjang','pumgye'])
    parser.add_argument('--binary',required=True,type=Path)
    parser.add_argument('--revision',required=True)
    args=parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',args.revision):
        raise SystemExit('full qualified source revision required')
    binary=args.binary.resolve(strict=True)
    program=subprocess.run(['readelf','-lW',str(binary)],check=True,capture_output=True).stdout
    if b'INTERP' in program:
        raise SystemExit('dynamic-loader binaries are not accepted')
    image=f'hangang-world/{args.component}:{args.revision[:12]}'
    with tempfile.TemporaryDirectory(prefix='hangang-world-image-') as temporary:
        root=Path(temporary)
        shutil.copy2(binary,root/args.component)
        (root/'Dockerfile').write_text(f'FROM scratch\nCOPY --chmod=0555 {args.component} /{args.component}\nUSER 65532:65532\nENTRYPOINT ["/{args.component}"]\n')
        subprocess.run(['docker','build','--network=none','--label','org.opencontainers.image.revision='+args.revision,'--tag',image,str(root)],check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',image,'--version'],check=True)
    inspected=json.loads(subprocess.check_output(['docker','image','inspect',image]))[0]
    print(json.dumps({'image':image,'id':inspected['Id'],'bytes':inspected['Size'],'declared_source_revision':args.revision}))


if __name__=='__main__':main()
