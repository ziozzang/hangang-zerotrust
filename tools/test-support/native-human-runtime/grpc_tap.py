#!/usr/bin/env python3
"""Qualification-only authenticated raw unary transport; grants no authority."""
import argparse
import time
import asyncio
import contextlib
import hmac
import ipaddress
import json
import math
import os
import signal
import stat
from pathlib import Path
import sys
import tempfile

import grpc

METHODS = {
    '/hangang.hopae.v1.Authentication/Verify': 32768,
    '/hangang.hopae.v1.HumanAuthenticationReceipts/IssueObserved': 32768,
    '/hangang.hopae.v1.HumanAuthenticationReceipts/ObserveTime': 4096,
    '/hangang.hopae.v1.HumanObservedCredentialProjection/Project': 8448,
    '/hangang.pumgye.v1.HumanObservedProjectionPermits/Observe': 8192,
    '/hangang.pumgye.v1.Authorization/Decide': 2048,
    '/hangang.pumgye.v1.HumanResourceAuthorization/Decide': 2048,
    '/hangang.pumgye.v1.HumanObservedProjectionPermits/Issue': 8192,
}
MAX_REPLY = 32768
MAX_RECEIVE = 65536  # Transport allocation bound; exact method caps remain lower.


def read_private(path, maximum, secret=False):
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or (secret and info.st_mode & 0o077):
            raise ValueError('private regular input required')
        with os.fdopen(descriptor, 'rb', closefd=False) as stream:
            data = stream.read(maximum + 1)
    finally:
        os.close(descriptor)
    if not data or len(data) > maximum:
        raise ValueError('invalid private input')
    return data


def token(path):
    data = read_private(path, 256, secret=True)
    if len(data) < 32 or any(c < 33 or c > 126 for c in data):
        raise ValueError('invalid caller file')
    return b'Bearer ' + data


def endpoint(value):
    # Never resolve arbitrary DNS or contact operating services by default.
    host, port = value.rsplit(':', 1)
    if not ipaddress.ip_address(host).is_loopback or not port.isdecimal() or not 1 <= int(port) <= 65535:
        raise ValueError('owned loopback endpoint required')
    return value


def atomic_json(path, value):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.tap-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Tap(grpc.GenericRpcHandler):
    """One fixed upstream per allowed method, no protobuf parsing or mutation."""
    def __init__(self, config):
        if set(config) - {'qualification'} != {'listen', 'tls', 'inbound_caller_file', 'upstreams', 'maximum_inflight'}:
            raise ValueError('invalid tap configuration')
        self.listen = endpoint(config['listen'])
        self.inbound = token(config['inbound_caller_file'])
        if type(config['maximum_inflight']) is not int or not 1 <= config['maximum_inflight'] <= 128:
            raise ValueError('invalid capacity')
        tls = config['tls']
        if set(tls) != {'ca', 'certificate', 'key'}:
            raise ValueError('invalid server TLS')
        self.server_credentials = grpc.ssl_server_credentials(
            [(read_private(tls['key'], 131072), read_private(tls['certificate'], 131072))],
            root_certificates=read_private(tls['ca'], 131072), require_client_auth=True)
        self.routes = {}
        self.channels = []
        self.route_channels = {}
        self.replay_transport = {'prepared':False,'elapsed_boottime_ns':None}
        self.replay_transport_attempted = False
        self.inflight = 0
        self.capacity = config['maximum_inflight']
        self.counts = {name: {'received': 0, 'forwarded': 0, 'ok': 0, 'refused': 0} for name in config['upstreams']}
        if not config['upstreams'] or not set(config['upstreams']) <= METHODS.keys():
            raise ValueError('unknown method')
        prepared = []
        for name, spec in config['upstreams'].items():
            if set(spec) != {'endpoint', 'server_name', 'ca', 'certificate', 'key', 'caller_file'}:
                raise ValueError('invalid upstream')
            if spec['server_name'] != 'localhost':
                raise ValueError('owned TLS server name required')
            outbound = token(spec['caller_file'])
            if hmac.compare_digest(outbound, self.inbound):
                raise ValueError('distinct caller credentials required')
            prepared.append((name, endpoint(spec['endpoint']), outbound,
                read_private(spec['ca'], 131072), read_private(spec['key'], 131072),
                read_private(spec['certificate'], 131072)))
        self.hooks = None
        if 'qualification' in config:
            from grpc_tap_hooks import Hooks
            self.hooks = Hooks(config['qualification'],config['upstreams'],read_private)
        # All file/configuration checks finish before any channel allocation.
        for name, address, outbound, ca, key, certificate in prepared:
            creds = grpc.ssl_channel_credentials(ca, key, certificate)
            channel = grpc.aio.secure_channel(address, creds, options=(
                ('grpc.ssl_target_name_override', 'localhost'), ('grpc.enable_retries', 0),
                ('grpc.max_receive_message_length', MAX_REPLY), ('grpc.max_send_message_length', METHODS[name])))
            self.channels.append(channel)
            self.route_channels[name] = channel
            self.routes[name] = (channel.unary_unary(name), outbound)
        self.server = None

    async def call(self, name, raw, context):
        remaining = context.time_remaining()
        if remaining is None or not math.isfinite(remaining) or remaining <= 0 or len(raw) > METHODS[name]:
            raise ValueError('original bounded call refused')
        rpc, caller = self.routes[name]
        reply = await rpc(raw, timeout=min(remaining,1.0), metadata=(('authorization',caller.decode()),))
        if len(reply) > MAX_REPLY:
            raise ValueError('upstream reply limit')
        return reply

    def service(self, details):
        name = details.method
        if name not in self.routes:
            return None
        async def forward(raw, context):
            count = self.counts[name]
            count['received'] += 1
            credentials = [v for k, v in context.invocation_metadata() if k == 'authorization']
            if len(credentials) != 1 or not hmac.compare_digest(credentials[0].encode(), self.inbound):
                count['refused'] += 1
                await context.abort(grpc.StatusCode.UNAUTHENTICATED, 'tap caller refused')
            remaining = context.time_remaining()
            if remaining is None or not math.isfinite(remaining) or remaining <= 0:
                count['refused'] += 1
                await context.abort(grpc.StatusCode.DEADLINE_EXCEEDED, 'original deadline required')
            if len(raw) > METHODS[name]:
                count['refused'] += 1
                await context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, 'tap frame limit')
            if self.inflight >= self.capacity:
                count['refused'] += 1
                await context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, 'tap capacity')
            self.inflight += 1
            # Capture once before any upstream await. Arming affects only future calls.
            hooks = self.hooks if self.hooks is not None and self.hooks.armed else None
            started = None
            try:
                if hooks is not None:
                    try:
                        raw = hooks.mutate(name,raw)
                    except Exception as error:
                        if isinstance(error,grpc.aio.AioRpcError):hooks.status(error.code())
                        hooks.counts['failed'] += 1
                        await context.abort(grpc.StatusCode.FAILED_PRECONDITION,'tap qualification refused')
                if len(raw) > METHODS[name]:
                    count['refused'] += 1
                    await context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED,'tap mutated frame limit')
                count['forwarded'] += 1
                started = hooks.now() if hooks is not None and hooks.mode == 'exact_pair_replay' else None
                if started is not None and name == '/hangang.hopae.v1.HumanObservedCredentialProjection/Project':
                    hooks.step('first_project',started,context)
                reply = await self.call(name,raw,context)
                if hooks is not None and hooks.mode == 'exact_pair_replay' and name == '/hangang.hopae.v1.HumanObservedCredentialProjection/Project':
                    try:
                        reply = await hooks.replay(raw,reply,started,self.call,context)
                    except Exception as error:
                        if isinstance(error,grpc.aio.AioRpcError):hooks.status(error.code())
                        hooks.counts['failed'] += 1
                        count['refused'] += 1
                        await context.abort(grpc.StatusCode.FAILED_PRECONDITION,'tap qualification refused')
                count['ok'] += 1
                return reply
            except asyncio.CancelledError:
                if started is not None and hooks is not None and hooks.mode=='exact_pair_replay' and name=='/hangang.hopae.v1.HumanObservedCredentialProjection/Project':
                    hooks.cancelled(started,context)
                raise
            except grpc.aio.AioRpcError as error:
                if hooks is not None and hooks.mode=='exact_pair_replay' and name=='/hangang.hopae.v1.HumanObservedCredentialProjection/Project':
                    hooks.status(error.code())
                count['refused'] += 1
                await context.abort(error.code(), 'upstream refused')
            finally:
                self.inflight -= 1
        return grpc.unary_unary_rpc_method_handler(forward)

    async def start(self):
        self.server = grpc.aio.server(options=(('grpc.max_receive_message_length', MAX_RECEIVE),
            ('grpc.max_send_message_length', MAX_REPLY)), maximum_concurrent_rpcs=self.capacity)
        self.server.add_generic_rpc_handlers((self,))
        if not self.server.add_secure_port(self.listen, self.server_credentials):
            raise ValueError('tap bind failed')
        await self.server.start()

    async def close(self):
        if self.server is not None:
            await self.server.stop(0)
            await self.server.wait_for_termination()
        for channel in self.channels:
            await channel.close()
        if self.hooks is not None:
            self.hooks.cookie = None

    def control(self,command):
        if command=={'op':'snapshot'}:
            return self.snapshot()
        if command=={'op':'arm'}:
            return self.arm()
        if command=={'op':'shutdown'}:
            return {'ok':True,'op':'shutdown'}
        raise ValueError('invalid control command')

    async def prepare_replay_transport(self):
        op='prepare_replay_transport'
        if self.hooks is None or self.hooks.mode!='exact_pair_replay':
            return {'ok':False,'op':op,'stage':'not_configured'}
        if self.hooks.armed:
            return {'ok':False,'op':op,'stage':'armed'}
        if self.replay_transport_attempted:
            return {'ok':False,'op':op,'stage':'already_attempted'}
        self.replay_transport_attempted=True
        try:
            started=time.clock_gettime_ns(time.CLOCK_BOOTTIME)
            await asyncio.wait_for(self.route_channels['/hangang.pumgye.v1.HumanObservedProjectionPermits/Observe'].channel_ready(),timeout=1.0)
            elapsed=time.clock_gettime_ns(time.CLOCK_BOOTTIME)-started
            if elapsed<0:raise ValueError('clock')
        except asyncio.CancelledError:
            raise
        except Exception:
            return {'ok':False,'op':op,'stage':'transport'}
        self.replay_transport={'prepared':True,'elapsed_boottime_ns':elapsed}
        return {'ok':True,'op':op,**self.replay_transport}

    def arm(self):
        if self.hooks is None:
            return {'ok':False,'op':'arm','stage':'not_configured'}
        if not self.hooks.arm():
            return {'ok':False,'op':'arm','stage':'already_armed'}
        return {'ok':True,'op':'arm','armed':True}

    def snapshot(self):
        result = {'contract': 'qualification-grpc-tap-v1', 'inflight': self.inflight,
                  'stages': {k: dict(v) for k, v in self.counts.items()}}
        if self.hooks is not None:
            result['qualification'] = self.hooks.snapshot()
            result['qualification']['replay_transport'] = dict(self.replay_transport)
        return result


async def main(args):
    parent = os.getppid()
    ready_parent = Path(args.ready).parent.stat()
    if ready_parent.st_uid != os.getuid() or ready_parent.st_mode & 0o077 or Path(args.ready).exists():
        raise ValueError('fresh ready path in owned private directory required')
    tap = Tap(json.loads(read_private(args.config, 131072, secret=True)))
    loop = asyncio.get_running_loop()
    task = asyncio.current_task()
    loop.add_signal_handler(signal.SIGTERM, task.cancel)
    async def parent_watch():
        while True:
            await asyncio.sleep(0.2)
            if os.getppid() != parent:
                task.cancel()
                return
    watcher = asyncio.create_task(parent_watch())
    transport = None
    try:
        reader = asyncio.StreamReader(limit=1024)
        transport, _ = await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)
        await tap.start()
        atomic_json(args.ready, {'contract': 'qualification-grpc-tap-v1', 'endpoint': tap.listen})
        while True:
            line = await reader.readline()
            if not line:
                break
            command = json.loads(line)
            reply=await tap.prepare_replay_transport() if command=={'op':'prepare_replay_transport'} else tap.control(command)
            print(json.dumps(reply), flush=True)
            if command == {'op':'shutdown'}:
                break
    finally:
        watcher.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await watcher
        if transport is not None:
            transport.close()
        await tap.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--ready', required=True)
    try:
        asyncio.run(main(parser.parse_args()))
    except (Exception, asyncio.CancelledError):
        print('{"ok":false,"stage":"tap"}', file=sys.stderr)
        raise SystemExit(1)
