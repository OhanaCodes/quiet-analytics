"""Prove the masking works, before trusting it.

Starts an isolated nginx on loopback using this repository's own map file, feeds it synthetic
addresses, and checks that what nginx would log is the masked network and nothing else. The test
instance substitutes a header for $remote_addr so addresses can be driven from the test; that
substitution exists only here and never in the installed configuration.

    python3 tests/test-masking.py
"""
from pathlib import Path
import ipaddress, random, subprocess, tempfile, time, urllib.request

source = (Path(__file__).resolve().parent.parent / 'nginx' / '00-quiet-analytics.conf').read_text()

with tempfile.TemporaryDirectory(prefix='qa-nginx-test-') as d:
    p = Path(d); p.chmod(0o755)
    config = (f'pid {d}/nginx.pid;\nerror_log /dev/null;\nevents {{}}\nhttp {{\n'
              + source.replace('map $remote_addr $qa_network', 'map $http_x_test_ip $qa_network')
              + '\nserver { listen 127.0.0.1:18997; access_log off;'
                ' location / { return 200 "$qa_network|$qa_target|$qa_referrer"; } }\n}')
    (p / 'nginx.conf').write_text(config)
    command = ['nginx', '-p', d, '-c', str(p / 'nginx.conf')]
    subprocess.run(command + ['-t'], check=True)
    subprocess.run(command, check=True)
    try:
        samples = ['192.0.2.199', '203.0.113.255', '::1', '::', '2001:db8::1', '2001::abcd',
                   '::1234:5678:90ab:cdef:1234:5678', '2001:db8:1234:ffff:ffff:ffff:ffff:ffff',
                   '::ffff:192.0.2.199']
        rng = random.Random(29)
        samples += [str(ipaddress.IPv6Address(rng.getrandbits(128))) for _ in range(100)]

        for address in samples:
            request = urllib.request.Request(
                'http://127.0.0.1:18997/?secret=not-retained',
                headers={'X-Test-IP': address, 'Referer': 'https://example.org/private?secret=also-not'})
            for _ in range(10):
                try:
                    with urllib.request.urlopen(request) as r:
                        got, target, ref = r.read().decode().split('|')
                    break
                except ConnectionRefusedError:
                    time.sleep(.05)
            ip = ipaddress.ip_address(address)
            if getattr(ip, 'ipv4_mapped', None):
                ip = ip.ipv4_mapped
            expected = ipaddress.ip_network(f'{ip}/{24 if ip.version == 4 else 48}',
                                            strict=False).network_address
            assert ipaddress.ip_address(got) == expected, (address, got, expected)
            assert target == '/', (address, target)
            assert ref == 'https://example.org/', (address, ref)   # domain only, no path, no query

        # An unlisted path must not reach the log, and an IP-literal referrer is dropped entirely.
        request = urllib.request.Request(
            'http://127.0.0.1:18997/a-path-with-a-person-in-it?q=secret',
            headers={'X-Test-IP': '192.0.2.199', 'Referer': 'https://192.0.2.199/person'})
        with urllib.request.urlopen(request) as r:
            assert r.read().decode() == '192.0.2.0|/other|-'

        print(f'PASS: {len(samples)} IPv4/IPv6 masks, unlisted paths grouped, referrers reduced to domain')
    finally:
        subprocess.run(command + ['-s', 'quit'], check=True)
