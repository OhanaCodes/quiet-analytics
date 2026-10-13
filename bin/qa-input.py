"""Bounded streaming input: feed retained access logs to the report, oldest first.

Aborts above 64 MiB of expanded log rather than letting a traffic spike or a rotation mistake
turn the nightly batch into an unbounded job. The previous report is kept on abort.
"""
from pathlib import Path
import gzip
import os
import sys

LOG = Path(os.environ.get('QA_LOG', '/var/log/nginx/quiet.access.log'))
LIMIT = int(os.environ.get('QA_LIMIT_MIB', '64')) * 1024 * 1024

paths = list(LOG.parent.glob(LOG.name + '*'))

def age(p):
    suffix = p.name.removeprefix(LOG.name).removesuffix('.gz')
    return int(suffix[1:]) if suffix else 0

used = 0
for path in sorted(paths, key=age, reverse=True):
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rb') as stream:
        for line in stream:
            used += len(line)
            if used > LIMIT:
                sys.exit(f'Expanded input exceeds {LIMIT // 1048576} MiB; previous report retained. '
                         'Review traffic or log retention.')
            sys.stdout.buffer.write(line)
