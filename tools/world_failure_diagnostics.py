"""Private, bounded world-fixture diagnostics. Never read Secret/config/env values."""
import json
import re
import sys
import subprocess


def snapshot(kube):
    nodes = json.loads(kube('get', 'nodes', '-o', 'json'))['items']
    pods = json.loads(kube('get', 'pods', '-A', '-o', 'json'))['items']
    return {'nodes': {n['metadata']['uid']: any(c['type'] == 'Ready' and c['status'] == 'True' for c in n['status'].get('conditions', [])) for n in nodes},
            'pods': {p['metadata']['uid']: p['status'].get('phase') for p in pods}}


def redact(text, secrets):
    for secret in sorted((s for s in secrets if s), key=len, reverse=True):
        text = text.replace(secret, '[redacted]')
    text = re.sub(r'-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----', '[redacted key]', text, flags=re.S)
    text = re.sub(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[redacted jwt]', text)
    return text[-65536:]


def capture(kube, namespace, namespace_uid, directory, secrets):
    """Capture exact owned namespace before cleanup; failures never replace primary."""
    if not directory or not namespace_uid:
        return
    current = json.loads(kube('get', 'namespace', namespace, '-o', 'json'))
    if current['metadata']['uid'] != namespace_uid:
        raise RuntimeError('diagnostic namespace UID replaced')
    pods = json.loads(kube('-n', namespace, 'get', 'pods', '-o', 'json'))['items']
    result = []
    for pod in pods:
        meta = pod['metadata']; statuses = []
        for status in pod['status'].get('initContainerStatuses', []) + pod['status'].get('containerStatuses', []):
            def state(value):
                return {kind: {k: v for k, v in fields.items() if k in {'exitCode', 'signal', 'reason', 'startedAt', 'finishedAt', 'containerID'}} for kind, fields in value.items()}
            statuses.append({'name': status['name'], 'restartCount': status.get('restartCount'), 'ready': status.get('ready'), 'image': status.get('image'), 'imageID': status.get('imageID'), 'state': state(status.get('state', {})), 'lastState': state(status.get('lastState', {}))})
        result.append({'name': meta['name'], 'uid': meta['uid'], 'namespace_uid': namespace_uid, 'phase': pod['status'].get('phase'), 'containers': statuses})
    (directory/'pods-before-cleanup.json').write_text(json.dumps(result, indent=2)+'\n')
    for pod in result:
        for container in pod['containers']:
            for previous in [False, True]:
                # Refuse a same-name replacement between status and log request.
                current = json.loads(kube('-n', namespace, 'get', 'pod', pod['name'], '-o', 'json'))
                if current['metadata']['uid'] != pod['uid']:
                    continue
                try:
                    args = ['-n', namespace, 'logs', pod['name'], '-c', container['name'], '--tail=200', '--limit-bytes=65536']
                    if previous: args.append('--previous')
                    text = redact(kube(*args, timeout=10).decode(errors='replace'), secrets)
                    current_namespace = json.loads(kube('get', 'namespace', namespace, '-o', 'json'))
                    current_pod = json.loads(kube('-n', namespace, 'get', 'pod', pod['name'], '-o', 'json'))
                    if current_namespace['metadata']['uid'] != namespace_uid or current_pod['metadata']['uid'] != pod['uid']:
                        continue
                    (directory/(pod['uid']+'-'+container['name']+('-previous' if previous else '-current')+'.log')).write_text(text)
                except Exception:
                    pass


def finish(steps, baseline, kube, directory):
    """Run all cleanup and baseline checks; preserve active primary exception."""
    primary = sys.exc_info()[1]
    errors = []
    for name, step in steps:
        try: step()
        except Exception as error: errors.append({'step': name, 'error_type': type(error).__name__})
    try:
        after = snapshot(kube)
        unchanged = after['nodes'] == baseline['nodes'] and all(after['pods'].get(uid) == phase for uid, phase in baseline['pods'].items())
        if not unchanged: errors.append({'step': 'baseline', 'error_type': 'BaselineChanged'})
    except Exception as error:
        errors.append({'step': 'baseline', 'error_type': type(error).__name__})
    facts = {'primary_error_type': type(primary).__name__ if primary else None, 'cleanup_errors': errors, 'baseline_checked': True}
    if directory:
        try: (directory/'cleanup-facts.json').write_text(json.dumps(facts, indent=2)+'\n')
        except Exception as error:
            errors.append({'step': 'evidence', 'error_type': type(error).__name__})
    print('Owned cleanup facts: '+json.dumps(facts, sort_keys=True), flush=True)
    if errors and primary is None:
        raise RuntimeError('owned cleanup or baseline verification failed')


def cleanup_forwards(processes):
    errors = []
    for process in processes:
        try:
            process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait()
        except Exception as error:
            errors.append(type(error).__name__)
    if errors:
        raise RuntimeError('owned forward cleanup failed')


def cleanup_namespace(kube, namespace, uid):
    current = json.loads(kube('get', 'namespace', namespace, '-o', 'json'))
    if current['metadata']['uid'] != uid:
        raise RuntimeError('owned namespace UID replaced')
    options = {'apiVersion': 'v1', 'kind': 'DeleteOptions', 'preconditions': {'uid': uid, 'resourceVersion': current['metadata']['resourceVersion']}}
    kube('delete', '--raw', '/api/v1/namespaces/'+namespace, '-f', '-', body=json.dumps(options).encode())
    kube('wait', '--for=delete', 'namespace/'+namespace, '--timeout=120s', timeout=135)
