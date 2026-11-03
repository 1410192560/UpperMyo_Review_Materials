"""Verify the distributed materials against their package SHA-256 manifest."""
from pathlib import Path
from pathlib import PurePosixPath, PureWindowsPath
import hashlib
import json
import re
import sys

root = Path(__file__).resolve().parents[1].resolve()


def package_path(name):
    if (not isinstance(name, str) or not name or '\\' in name or ':' in name
            or PurePosixPath(name).is_absolute() or PureWindowsPath(name).anchor
            or '..' in PurePosixPath(name).parts or '\x00' in name):
        raise ValueError('Invalid package-manifest path: ' + repr(name))
    relative = Path(name)
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root) or relative.as_posix() != name:
        raise ValueError('Package-manifest path escapes or aliases the package: ' + name)
    return candidate


def main():
    expected = {}
    resolved_names = set()
    for line in (root / 'SHA256SUMS').read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():
            continue
        if '  ' not in line:
            raise ValueError('Malformed SHA256SUMS line')
        digest, name = line.split('  ', 1)
        path = package_path(name)
        identity = str(path).casefold()
        if not re.fullmatch(r'[a-fA-F0-9]{64}', digest) or identity in resolved_names:
            raise ValueError('Invalid or duplicate checksum entry: ' + name)
        expected[name] = digest.lower()
        resolved_names.add(identity)
    if not expected:
        raise ValueError('SHA256SUMS contains no file entries')

    manifest = json.loads((root / 'release_manifest.json').read_text(encoding='utf-8-sig'))
    entries = manifest.get('files')
    if not isinstance(entries, list) or not entries:
        raise ValueError('release_manifest.json contains no file entries')
    declared = {}
    for entry in entries:
        name = entry['path']
        package_path(name)
        digest = entry['sha256']
        if name in declared or not re.fullmatch(r'[a-fA-F0-9]{64}', digest):
            raise ValueError('Invalid release-manifest entry: ' + name)
        declared[name] = digest.lower()
    if set(expected) != set(declared) | {'release_manifest.json'}:
        raise ValueError('SHA256SUMS does not cover the complete release manifest')
    if any(expected[name] != digest for name, digest in declared.items()):
        raise ValueError('The two file manifests contain inconsistent checksums')

    errors = []
    for name, digest in expected.items():
        path = package_path(name)
        if not path.is_file():
            errors.append('Missing: ' + name)
            continue
        actual = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                actual.update(chunk)
        if actual.hexdigest() != digest:
            errors.append('Checksum mismatch: ' + name)
    for error in errors:
        print(error)
    print(f'Checked {len(expected)} package files; {len(errors)} error(s).')
    return 1 if errors else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError, TypeError, OSError) as error:
        print('Package verification failed: ' + str(error))
        sys.exit(1)
