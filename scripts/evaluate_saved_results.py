"""Evaluate supplied saved predictions and paired repeats. No training/data paths.

Usage: python evaluate_saved_results.py
Requires Python >=3.10 and NumPy. Classification scores are proportions here;
multiply by 100 for percentage points in manuscript tables.
"""

import math

def require(condition, message):
    if not condition:
        raise ValueError(message)

from pathlib import Path
import csv,json
from collections import defaultdict
import numpy as np

HERE=Path(__file__).resolve().parents[1]
RESULTS=HERE/'results'
OUT=HERE/'verification';OUT.mkdir(exist_ok=True)
def rows(name):
 with (RESULTS/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def save(name,data):
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
def metrics(cm):
 tp=np.diag(cm);den=cm.sum(0)+cm.sum(1)
 f1=np.divide(2*tp,den,out=np.zeros(9),where=den>0)
 recalls=np.divide(tp,cm.sum(1),out=np.zeros(9),where=cm.sum(1)>0)
 return f1,recalls

pred=rows('internal_predictions.csv')
models=['LDA','SVM','RF','CNN','CORAL','ProtoNet'];internal=[]

# Validate the sample identities and class indices before indexing NumPy arrays.
with (HERE/'indices/sample_index.csv').open(encoding='utf-8-sig', newline='') as f:
 sample_index=list(csv.DictReader(f))
label_order=json.loads((HERE/'configurations/data_dictionary.json').read_text(encoding='utf-8-sig'))['label_order']
require(len(pred)==len(sample_index)==2640, 'Expected 2,640 indexed predictions')
require([int(r['sample_id']) for r in sample_index]==list(range(2640)), 'Sample indices must be unique and ordered')
require(len(label_order)==9, 'Expected nine recognition labels')
for row,sample in zip(pred,sample_index):
 require((row['sample_id'],row['subject'])==(sample['sample_id'],sample['subject']), 'Prediction/sample identity mismatch')
 for key in ['true_class',*models]:
  require(0<=int(row[key])<9, 'Class indices must be integers from 0 to 8')
 require(label_order[int(row['true_class'])]==sample['label'], 'Prediction truth does not match sample label')
for name in models:
 cm=np.zeros((9,9),dtype=int)
 for row in pred:cm[int(row['true_class']),int(row[name])]+=1
 f1,rec=metrics(cm)
 internal.append(dict(model=name,nine_class_macro_f1=float(f1.mean()),eight_action_class_macro_f1_from_full_matrix=float(f1[:8].mean()),true_action_subset_accuracy=float(np.trace(cm[:8,:8])/cm[:8].sum()),background_recall=float(rec[8])))
 if name=='CNN':
  with (OUT/'CNN_integer_confusion.csv').open('w',newline='') as f:csv.writer(f).writerows(cm)
save('recognition_summaries.csv',internal)

classification=rows('classification_paired_repeats.csv');force=rows('force_paired_repeats.csv')

require(len({(r['task'],r['budget'],r['seed'],r['subject']) for r in classification})==len(classification), 'Duplicate classification paired-result key')
for row in classification:
 require(row['task'] in ['WristMotion','Izmir9','ADL6'], 'Unexpected classification task')
 require(all(math.isfinite(float(row[k])) for k in ['target_only','transfer','gain']), 'Classification scores must be finite')
 require(all(0<=float(row[k])<=1 for k in ['target_only','transfer']), 'Classification proportions must be between 0 and 1')
 require(abs(float(row['transfer'])-float(row['target_only'])-float(row['gain']))<1e-12, 'Inconsistent paired classification gain')
require(len({(r['seed'],r['budget'],r['arm'],r['subject']) for r in force})==len(force), 'Duplicate force-result key')
for row in force:
 require(row['arm'] in ['target_only','fine_tune'], 'Unexpected force condition')
 require(all(math.isfinite(float(row[k])) for k in ['r2','mae_N','rmse_N']), 'Force scores must be finite')
 require(0<=float(row['mae_N'])<=float(row['rmse_N'])+1e-12, 'Invalid force error values')
for seed,budget,subject in {(r['seed'],r['budget'],r['subject']) for r in force}:
 require({r['arm'] for r in force if (r['seed'],r['budget'],r['subject'])==(seed,budget,subject)}=={'target_only','fine_tune'}, 'Missing paired force condition')
paired=[]
for task in ['WristMotion','Izmir9','ADL6']:
 data=[r for r in classification if r['task']==task]
 for budget in [min(int(r['budget']) for r in data),max(int(r['budget']) for r in data)]:
  groups=defaultdict(list)
  for row in data:
   if int(row['budget'])==budget:groups[row['subject']].append(row)
  for sid,rr in sorted(groups.items()):
   a=np.array([float(r['target_only']) for r in rr]);b=np.array([float(r['transfer']) for r in rr]);delta=b-a
   paired.append(dict(task=task,budget=budget,subject=sid,repeats=len(rr),target=float(a.mean()),transfer=float(b.mean()),gain=float(delta.mean()),repeat_sd_gain=float(delta.std(ddof=1)) if len(rr)>1 else 0.,unit='proportion'))
for budget in [10,10775]:
 data=[r for r in force if int(r['budget'])==budget]
 for sid in sorted({r['subject'] for r in data}):
  aa={r['seed']:float(r['r2']) for r in data if r['subject']==sid and r['arm']=='target_only'}
  bb={r['seed']:float(r['r2']) for r in data if r['subject']==sid and r['arm']=='fine_tune'}
  require(set(aa)==set(bb), 'Failed validation: set(aa)==set(bb)')
  a=np.array([aa[k] for k in sorted(aa)]);b=np.array([bb[k] for k in sorted(aa)]);delta=b-a
  paired.append(dict(task='FCU',budget=budget,subject=sid,repeats=len(a),target=float(a.mean()),transfer=float(b.mean()),gain=float(delta.mean()),repeat_sd_gain=float(delta.std(ddof=1)),unit='R2'))
save('participant_paired_effects.csv',paired)
summary=[]
for task in ['WristMotion','Izmir9','ADL6','FCU']:
 for budget in sorted({r['budget'] for r in paired if r['task']==task}):
  rr=[r for r in paired if r['task']==task and r['budget']==budget];a=np.array([r['gain'] for r in rr]);lo=hi=''
  if len(a)>=5:
   boot=a[np.random.default_rng(20261029).integers(0,len(a),(20000,len(a)))].mean(1)
   lo,hi=(float(x) for x in np.quantile(boot,[.025,.975]))
  summary.append(dict(task=task,budget=budget,n_subjects=len(a),mean_gain=float(a.mean()),min_person_gain=float(a.min()),max_person_gain=float(a.max()),descriptive_ci95_low=lo,descriptive_ci95_high=hi,positive_people=int((a>0).sum()),unit=rr[0]['unit']))
save('principal_effect_summary.csv',summary)

# Check generated summaries against the delivered tables at full precision.
expected=rows('principal_effect_summary.csv');checks=0
require(len(summary)==len(expected), 'Failed validation: len(summary)==len(expected)')
for a,b in zip(summary,expected):
 require(a['task']==b['task'] and a['budget']==int(b['budget']), "Failed validation: a['task']==b['task'] and a['budget']==int(b['budget'])")
 for key in ['mean_gain','min_person_gain','max_person_gain','descriptive_ci95_low','descriptive_ci95_high']:
  if b[key]=='':require(a[key]=='', "Failed validation: a[key]==''")
  else:require(np.isclose(float(a[key]),float(b[key]),atol=1e-12,rtol=0), (a['task'],a['budget'],key))
  checks+=1
expected=rows('internal_action_focused_metrics.csv')
require(len(internal)==len(expected), 'Failed validation: len(internal)==len(expected)')
for a,b in zip(internal,expected):
 require(a['model']==b['model'], "Failed validation: a['model']==b['model']")
 for key in a:
  if key!='model':require(np.isclose(a[key],float(b[key]),atol=1e-12,rtol=0), 'Failed validation: np.isclose(a[key],float(b[key]),atol=1e-12,rtol=0)');checks+=1
force_errors=[]
for budget in [10,10775]:
 for sid in ['lk','nk','pb','Mean']:
  rr=[r for r in force if int(r['budget'])==budget and (sid=='Mean' or r['subject']==sid)]
  row=dict(budget=budget,subject=sid)
  for arm,prefix in [('target_only','target'),('fine_tune','transfer')]:
   for metric in ['mae','rmse']:
    row[prefix+'_'+metric]=float(np.mean([float(r[metric+'_N']) for r in rr if r['arm']==arm]))
  force_errors.append(row)
save('force_error_N.csv',force_errors)
expected_errors=rows('force_error_N.csv')
require(len(force_errors)==len(expected_errors), 'Failed validation: len(force_errors)==len(expected_errors)')
for a,b in zip(force_errors,expected_errors):
 require(a['budget']==int(b['budget']) and a['subject']==b['subject'], "Failed validation: a['budget']==int(b['budget']) and a['subject']==b['subject']")
 for key in ['target_mae','transfer_mae','target_rmse','transfer_rmse']:
  require(np.isclose(a[key],float(b[key]),atol=1e-12,rtol=0), 'Failed validation: np.isclose(a[key],float(b[key]),atol=1e-12,rtol=0)');checks+=1
report=dict(status='PASS',n_internal_samples=len(pred),n_models=len(models),n_principal_effects=len(summary),numeric_checks=checks,independent_unit='participant; repetitions averaged within participant',bootstrap=dict(replicates=20000,seed=20261029))
(OUT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
