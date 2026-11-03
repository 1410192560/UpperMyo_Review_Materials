"""Recompute integer-confusion and seed-effect summaries from supplied saved results.

Python standard library only. No model training or MATLAB required.
"""

import math

def require(condition, message):
    if not condition:
        raise ValueError(message)

from pathlib import Path
import csv,json,statistics
HERE=Path(__file__).resolve().parents[1]
RESULTS=HERE/'results'
def read(name):
 with (RESULTS/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
raw=read('force_paired_repeats.csv');declared=read('fcu_pb_seed_effects.csv');gains=[]
require(len({(r['seed'],r['budget'],r['arm'],r['subject']) for r in raw})==len(raw), 'Duplicate force-result key')
require(len(declared)==3 and len({(r['seed'],r['budget'],r['subject']) for r in declared})==3, 'Expected three distinct paired seed effects')
for row in declared:
 records=[r for r in raw if r['seed']==row['seed'] and r['budget']==row['budget'] and r['subject']==row['subject']]
 a=next(float(r['r2']) for r in records if r['arm']=='target_only')
 b=next(float(r['r2']) for r in records if r['arm']=='fine_tune')
 require(abs(a-float(row['target_only_r2']))<1e-12 and abs(b-float(row['transfer_r2']))<1e-12, "Failed validation: abs(a-float(row['target_only_r2']))<1e-12 and abs(b-float(row['transfer_r2']))<1e-12")
 require(abs((b-a)-float(row['paired_gain']))<1e-12, "Failed validation: abs((b-a)-float(row['paired_gain']))<1e-12")
 gains.append(b-a)
with (RESULTS/'cnn_integer_confusion.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
cm=[[int(v) for v in row[1:]] for row in rows[1:]]

labels=['zq','zqq','zsz','wsz','wns','wwz','wq','wqq','none']
require(len(rows)==10 and all(len(row)==10 for row in rows), 'Expected a nine-by-nine confusion matrix')
require(rows[0][1:]==labels and [r[0] for r in rows[1:]]==labels, 'Unexpected confusion-matrix label order')
require(all(v>=0 for row in cm for v in row), 'Confusion counts must be nonnegative')
predicted=[[0]*9 for _ in range(9)]
for row in read('internal_predictions.csv'):
 true,pred=int(row['true_class']),int(row['CNN'])
 require(0<=true<9 and 0<=pred<9, 'Class indices must be integers from 0 to 8')
 predicted[true][pred]+=1
require(cm==predicted, 'Confusion matrix does not match the supplied predictions')
f1=statistics.mean(2*cm[i][i]/(sum(cm[i])+sum(r[i] for r in cm)) for i in range(9))
require(sum(map(sum,cm))==2640 and f'{f1:.4f}'=='0.9860', "Failed validation: sum(map(sum,cm))==2640 and f'{f1:.4f}'=='0.9860'")
result=dict(status='PASS',pb=dict(paired_seeds=len(gains),gains=gains,mean=statistics.mean(gains),sample_sd=statistics.stdev(gains),range=[min(gains),max(gains)]),cnn=dict(total=2640,macro_f1=f1,rounded_4dp=f'{f1:.4f}'))
out=HERE/'verification';out.mkdir(exist_ok=True)
(out/'additional_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
