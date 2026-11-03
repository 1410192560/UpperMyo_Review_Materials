"""Check support-set/test summaries from saved model-level metrics.

Standard library only. No model fitting or training.
"""

import math

def require(condition, message):
    if not condition:
        raise ValueError(message)

from pathlib import Path
from statistics import mean
import csv
import json

root = Path(__file__).resolve().parents[1]
rows = json.loads((root/'results/training_test_model_metrics.json').read_text(encoding='utf-8'))
with (root/'results/training_test_budget_metrics.csv').open(encoding='utf-8-sig', newline='') as f:
    declared = list(csv.DictReader(f))

require(len({(r['task'],r['budget'],r['repeat'],r['method']) for r in rows})==len(rows), 'Duplicate model-evaluation key')
require(len({(r['task'],r['budget']) for r in declared})==len(declared), 'Duplicate budget-summary key')
for row in rows:
    require(row['task'] in ['WristMotion','Izmir9','ADL6'] and row['method'] in ['target_only','fine_tune'], 'Unexpected task or model condition')
    require(int(row['train_samples'])==int(row['budget'])>0, 'Support size does not match budget')
    require(all(math.isfinite(float(row[k])) and 0<=float(row[k])<=1 for k in ['train_ba','train_accuracy','train_macro_f1','test_ba']), 'Evaluation proportions must be finite and between 0 and 1')
require(len(rows) == 2182 and len(declared) == 51, 'Failed validation: len(rows) == 2182 and len(declared) == 51')
require(len({(r['task'], r['budget']) for r in rows}) == 51, "Failed validation: len({(r['task'], r['budget']) for r in rows}) == 51")
checks = 0
for item in declared:
    for method in ['target_only', 'fine_tune']:
        values = [r for r in rows if r['task'] == item['task'] and r['budget'] == int(item['budget']) and r['method'] == method]
        require(len(values) == int(item[method+'_repeats']), "Failed validation: len(values) == int(item[method+'_repeats'])")
        for key in ['train_ba', 'train_accuracy', 'train_macro_f1', 'test_ba']:
            require(abs(mean(r[key] for r in values) - float(item[method+'_'+key])) < 1e-12, "Failed validation: abs(mean(r[key] for r in values) - float(item[method+'_'+key])) < 1e-12")
            checks += 1
result = dict(status='PASS', model_evaluations=len(rows), budget_rows=len(declared), numeric_comparisons=checks,
              scope='Reaggregation of saved support-set and test metrics; not model training or a complete training rerun.')
output = root/'verification'
output.mkdir(exist_ok=True)
(output/'training_test_verification.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, indent=2))
