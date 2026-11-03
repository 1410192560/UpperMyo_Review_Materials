"""Check the recording files against the manuscript benchmark manifest.

No model fitting or training.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

MATERIALS = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data-root', type=Path, required=True, help='Local 六通道数据集 directory downloaded from the separate data repository')
parser.add_argument('--output', type=Path)
args = parser.parse_args()
manifest_name = 'record_manifest.csv'
data_root = args.data_root.resolve()
if not data_root.is_dir():
    raise ValueError('--data-root must identify an existing data directory')
materials_root = MATERIALS.resolve()
output = (args.output or MATERIALS/'verification/data_links.json').resolve()
if output.suffix.lower() != '.json':
    raise ValueError('--output must be a JSON report path')
if output.is_relative_to(data_root):
    raise ValueError('The report must be outside the raw-data directory')
verification_root = (MATERIALS/'verification').resolve()
if args.output is None and not output.is_relative_to(materials_root):
    raise ValueError('The default report directory must remain inside the materials folder')
if output.is_relative_to(materials_root) and not output.is_relative_to(verification_root):
    raise ValueError('Reports inside the materials folder must be placed in verification/')
with (MATERIALS/'indices'/manifest_name).open(encoding='utf-8-sig', newline='') as f:
    records = list(csv.DictReader(f))
if len(records) != 264 or len({(r['subject'], r['record']) for r in records}) != 264:
    raise ValueError('The record manifest must contain 264 distinct records')
matches, issues = 0, []
for record in records:
    for filename, key in [('all_data_output.csv', 'all_sha256'), ('valid_data_output.csv', 'valid_sha256')]:
        relative = Path(f"subject_{record['subject']}")/record['record']/filename
        path = (data_root/relative).resolve()
        if not path.is_relative_to(data_root):
            raise ValueError('Data path escapes data root')
        actual = None
        if path.is_file():
            h = hashlib.sha256()
            with path.open('rb') as f:
                for chunk in iter(lambda: f.read(1024*1024), b''):
                    h.update(chunk)
            actual = h.hexdigest()
        if actual == record[key]:
            matches += 1
        else:
            issues.append(dict(subject=int(record['subject']), record=record['record'], path=relative.as_posix(),
                               expected_sha256=record[key], actual_sha256=actual,
                               issue='missing' if actual is None else 'hash_mismatch'))
report = dict(status='PASS' if not issues else 'DATA_LINK_MISMATCH',
              checked_manifest=manifest_name, records=len(records), csv_files_checked=len(records)*2,
              exact_path_and_hash_matches=matches, mismatches=issues,
              note='This check verifies recording-file identity; it does not train models.')
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k != 'mismatches'}, ensure_ascii=False, indent=2))
for issue in issues:
    print(issue['issue']+': '+issue['path'])
raise SystemExit(1 if issues else 0)
