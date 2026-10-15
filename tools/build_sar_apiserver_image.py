#!/usr/bin/env python3
"""Build only the reviewed capability-free API-server qualification derivative."""
import argparse,hashlib,io,json,os,pathlib,subprocess,tarfile,urllib.request
OFFICIAL='registry.k8s.io/kube-apiserver@sha256:1f207ab66b1ca6579dd5bf1024396015ca2a0f638157a7741d2d88d7b3c82c51'
LAYER='sha256:1e677224d9e973eef0efc3b0f34df71e4dab65f4bb4c0a80dbb35da0155d8ea8'
BINARY_SHA='de9b1b43c10143f448408b3aaf15f44fd5248b97a56301417a1fe2f1fc47a691'
CAP=b'\x01\x00\x00\x02\x00\x04'+bytes(14)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=pathlib.Path);a=p.parse_args();os.umask(0o077);a.output.mkdir(mode=0o700,parents=True,exist_ok=False)
 raw=urllib.request.urlopen('https://registry.k8s.io/v2/kube-apiserver/blobs/'+LAYER,timeout=60).read()
 if 'sha256:'+hashlib.sha256(raw).hexdigest()!=LAYER:raise ValueError('official layer bytes mismatch')
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*') as tar:
  member=tar.getmember('usr/local/bin/kube-apiserver');cap=member.pax_headers.get('SCHILY.xattr.security.capability','').encode('latin1');binary=tar.extractfile(member).read()
 if cap!=CAP or hashlib.sha256(binary).hexdigest()!=BINARY_SHA:raise ValueError('reviewed official binary/filecap mismatch')
 # A new ordinary file receives bytes, NOT OCI pax metadata or file attributes.
 staged=a.output/'kube-apiserver';staged.write_bytes(binary);staged.chmod(0o755)
 if 'security.capability' in os.listxattr(staged):raise ValueError('staging unexpectedly has file capability')
 dockerfile='FROM '+OFFICIAL+'\nCOPY --chmod=755 kube-apiserver /usr/local/bin/kube-apiserver\nUSER 65532:65532\n'
 (a.output/'Dockerfile').write_text(dockerfile);tag='sar-qualification/kube-apiserver:1.37.1-capfree-'+BINARY_SHA[:12]
 subprocess.run(['docker','build','--pull=false','-t',tag,str(a.output)],check=True,stdout=(a.output/'build-private.log').open('wb'),stderr=subprocess.STDOUT)
 image_id=subprocess.check_output(['docker','image','inspect',tag,'--format','{{.Id}}'],text=True).strip()
 # Verify the final container filesystem, not merely the build context.
 container=subprocess.check_output(['docker','create',tag],text=True).strip()
 try:
  exported=a.output/'rootfs-private.tar'
  subprocess.run(['docker','export','-o',str(exported),container],check=True)
  with tarfile.open(exported) as tar:
   final=tar.getmember('usr/local/bin/kube-apiserver')
   if any('capability' in k for k in final.pax_headers) or hashlib.sha256(tar.extractfile(final).read()).hexdigest()!=BINARY_SHA:raise ValueError('final binary capability/bytes mismatch')
  exported.unlink()
 finally:subprocess.run(['docker','rm',container],check=True,stdout=subprocess.DEVNULL)
 version=subprocess.check_output(['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--user','65532:65532','--entrypoint','/usr/local/bin/kube-apiserver',tag,'--version'],text=True).strip()
 if version!='Kubernetes v1.37.1':raise ValueError('actual constrained binary version mismatch')
 archive=a.output/'images.tar';subprocess.run(['docker','save','-o',str(archive),tag],check=True)
 with archive.open('rb') as f:archive_sha=hashlib.file_digest(f,'sha256').hexdigest()
 evidence={'schema_version':1,'kind':'reviewed-capability-free-apiserver','official_image':OFFICIAL,'official_layer':LAYER,'official_binary_sha256':BINARY_SHA,'official_filecap_hex':cap.hex(),'staged_capability_absent':True,'final_capability_absent':True,'final_binary_sha256':BINARY_SHA,'image_tag':tag,'config_id':image_id,'archive_sha256':archive_sha,'archive_bytes':archive.stat().st_size,'local_constrained_exec_version':version,'runtime_security_unchanged':'nonroot65532/dropALL/noPrivilegeEscalation; no extra capability','immutable_manifest_reference_pending_import':True}
 (a.output/'PROVENANCE.json').write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps({'output':str(a.output),'config_id':image_id,'archive_sha256':archive_sha}))
if __name__=='__main__':main()
