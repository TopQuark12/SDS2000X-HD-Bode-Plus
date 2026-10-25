#!/usr/bin/env python3
"""Explicit SCPI controls/export for a future hardware evaluation. Never flashes.
No connection is made unless this script is run with an instrument host.
"""
import argparse
import socket
from pathlib import Path

def receive_response(sock, limit=2*1024*1024):
    """Return either one text line or the exact IEEE-488.2 definite-length block."""
    def exact(n):
        out=bytearray()
        while len(out)<n:
            chunk=sock.recv(n-len(out))
            if not chunk:raise EOFError('Instrument closed connection mid-response')
            out.extend(chunk)
        return bytes(out)
    first=exact(1)
    if first==b'#':
        digit=exact(1)
        if digit not in b'123456789' or len(digit)!=1:raise ValueError('Expected definite-length IEEE block')
        field=exact(int(digit))
        if not field.isdigit():raise ValueError('Invalid IEEE length')
        n=int(field)
        if n>limit:raise ValueError('Response exceeds capacity')
        return exact(n),True
    data=bytearray(first)
    while not data.endswith(b'\n'):
        if len(data)>=limit:raise ValueError('Text response exceeds capacity')
        data.extend(exact(1))
    return bytes(data).rstrip(b'\r\n'),False

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host')
    parser.add_argument('action',choices=['status','capture','on','off','clear','export','thru','standard','fast','perf'])
    parser.add_argument('--port',type=int,default=5025)
    parser.add_argument('--timeout',type=float,default=30)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.action in ('export','thru') and args.output is None:parser.error('--output is required for export/thru')
    cmd={'export':'XCSV','thru':'XTHRU'}.get(args.action,'X'+args.action.upper())
    with socket.create_connection((args.host,args.port),timeout=args.timeout) as sock:
        sock.settimeout(args.timeout);sock.sendall(('BODE:DATA? '+cmd+'\n').encode())
        payload,block=receive_response(sock)
    if args.action in ('export','thru'):
        if not block:raise SystemExit(payload.decode(errors='replace'))
        # Exclusive create protects any pre-existing measurement file.
        with args.output.open('xb') as f:f.write(payload)
        print(f'Saved {len(payload)} bytes to {args.output}')
    else:print(payload.decode())

if __name__=='__main__':main()
