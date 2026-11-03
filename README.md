# UpperMyo Review Materials

These machine-readable files accompany the revised UpperMyo manuscript and are provided in a repository separate from the raw sEMG data. Keep this folder and its internal structure together. Obtain the recordings from the [UpperMyo data repository](https://github.com/HuangheZhang/UpperMyo). The manuscript and supplementary PDF provide the methods, equations and interpretation; they are not duplicated here.

## Directory layout

```text
workspace/
├── UpperMyo/                         # data repository, downloaded separately
│   └── 六通道数据集/
└── UpperMyo_Review_Materials/         # review-materials repository or extracted package
    ├── README.md
    ├── requirements.txt
    ├── SHA256SUMS
    ├── release_manifest.json
    ├── indices/
    ├── configurations/
    ├── results/
    └── scripts/
```

No raw sEMG files or external target datasets are duplicated in this folder. Obtain external data from the providers cited in the manuscript.

## File guide

| Directory/file | Contents |
|---|---|
| `indices/record_manifest.csv` | The manuscript benchmark's 264 recording identities, lengths, labels and SHA-256 checksums for full/valid CSVs. |
| `indices/sample_index.csv` | The ordered 2,640-sample benchmark: 1,320 action and 1,320 background windows, with source files and boundaries. |
| `indices/participant_class_counts.csv` | Per-participant counts in that benchmark. |
| `indices/participant_splits.json` | Internal outer/inner LOSO membership and external training, development and test participants. |
| `indices/temporal_flexion_events.csv` | 165 indexed positive temporal events, raw-file hashes, baseline and BB-reference indices. `raw_path` is relative to the data-repository root, not this materials repository. |
| `configurations/data_dictionary.json` | Channel order, label order, amplitude/timestamp units and index conventions. |
| `configurations/internal_configurations_by_fold.json` | Recognition search spaces, training settings and configurations selected within each outer-training fold. |
| `configurations/internal_selected_configuration_counts.csv` | Selection frequencies across the 24 outer folds. |
| `configurations/fixed_ablation_protocol.json` | Separate fixed-configuration channel-ablation settings, seeds and historical provenance hashes. |
| `configurations/wrist_*` | Actual support IDs, seeds and per-budget training schedules. |
| `configurations/fcu_protocol_metadata.json` | Final support/test membership and saved FCU protocol settings. |
| `configurations/temporal_final_config.json` | Author-confirmed temporal model/protocol configuration; storage references are relative to `configurations/`. |
| `results/internal_predictions.csv` | Saved nine-class predictions for six models; `sample_id` joins to `indices/sample_index.csv`. |
| `results/internal_*metrics.csv` | Participant summaries and action-focused summaries calculated from the same nine-class predictions. |
| `results/cnn_integer_confusion.csv` | Integer nine-class CNN confusion matrix. |
| `results/classification_paired_repeats.csv` | Per-participant/per-repeat target-only and transfer classification scores. |
| `results/force_paired_repeats.csv` | Per-participant/per-seed force R², MAE and RMSE. |
| `results/participant_paired_effects.csv`, `principal_effect_summary.csv`, `force_error_N.csv` | Reference summaries checked by the supplied evaluator. |
| `results/fcu_pb_seed_effects.csv` | Paired full-support seed effects for participant pb. |
| `results/force_trace_values.csv`, `force_trace_selection.json` | Selected complete force records and their performance-independent selection rule. |
| `results/izmir_action_group_results.csv` | Exact-match, related, unassociated and combined new-action summaries. |
| `results/wrist_development_test_comparison.csv` | Development/test summaries at 12 labeling budgets; not epoch histories or training-set accuracy. |
| `results/temporal_reported_results.csv` | Original reported temporal aggregate means and SDs; not newly generated predictions. |
| `results/temporal_positive_window_label_audit.csv` | Position checks for the 165 indexed positive windows against saved interval labels. |
| `scripts/evaluate_saved_results.py` | Recomputes recognition summaries, participant-paired effects and force errors. |
| `scripts/evaluate_additional_results.py` | Recomputes the CNN integer-matrix macro-F1 and pb seed-effect statistics. |
| `scripts/verify_package.py` | Verifies this folder's distributed files against `SHA256SUMS`. |
| `scripts/verify_data_links.py` | Verifies the exact raw-file paths and checksums referenced by the benchmark. |
| `results/training_test_budget_metrics.csv`, `training_test_model_metrics.json` | Support-set (resubstitution) and paired test metrics from 2,182 retained/restored model evaluations, summarized at 51 budgets for WristMotion, Izmir9 and ADL6. These support the current supplementary training/test table; they are not epoch histories or new training. |
| `scripts/evaluate_training_test_summaries.py` | Reaggregates the saved model-level metrics and checks the 51 budget summaries. |
| `release_manifest.json` | Original-file names/checksums and packaging transformations. |

## Run the checks

Use Python 3.10 or later. Open a terminal in `UpperMyo_Review_Materials/` (the directory containing this README), then run:

```sh
python -m pip install -r requirements.txt
python scripts/verify_package.py
python scripts/evaluate_saved_results.py
python scripts/evaluate_additional_results.py
python scripts/evaluate_training_test_summaries.py
python scripts/verify_data_links.py --data-root "../UpperMyo/六通道数据集"
```

Generated summaries and reports go to `verification/`; source files remain unchanged. MATLAB and a GPU are not needed for these checks. For data linkage, set `--data-root` to the actual local `六通道数据集` directory downloaded from the data repository. The example path above follows the example checkout layout; the repositories may be stored elsewhere. The saved-result evaluators do not require the raw-data repository.

Expected saved-result checks: 2,640 internal samples, six recognition models, eight principal task/budget effects and CNN macro-F1 0.9859656502687413 (0.9860 at four decimals). A successful saved-result check confirms these calculations, not a new model-training run.

## Identifiers, units and aggregation

- Recognition classes 0–8: `zq`, `zqq`, `zsz`, `wsz`, `wns`, `wwz`, `wq`, `wqq`, `none` (HO, EF, EE, WE, UD, RD, HC, WF, BG). Recognition background is class 8. The separate temporal task uses class 0 for rest and class 1 for association with a subsequent flexion event.
- Channels: BB, TB, ECR, ECU, FCR and FCU at 1,000 Hz; channel amplitudes are μV. Raw timestamps are μs; indexed times are seconds. No signal values are rescaled by this package.
- Sample indices are zero-based with an inclusive start and exclusive end. Physical CSV line numbers are one-based and include the header. `sample_index.csv` source-file paths are relative to `六通道数据集/`.
- Classification scores are proportions unless a column explicitly ends in `_percent`; multiply gains in proportions by 100 for percentage points. Force errors and traces are in newtons; R² and its paired differences are dimensionless.
- Computational repetitions are averaged within each participant before participant-level effects are summarized. Repeats and seeds are not additional participants.
- Eight-action summaries reuse the full nine-class predictions; they do not represent an independently trained eight-class model.

## Data linkage and execution scope

`indices/record_manifest.csv` identifies the 264 recordings used by the benchmark. `indices/sample_index.csv` locates the 2,640 analyzed windows, and `sample_id` links them to the saved recognition predictions. Use `verify_data_links.py --data-root PATH` to check the downloaded recordings against the manifest.

The temporal material contains the final configuration, positive-event indices and reported aggregate results. Original rest-pair indices, cue timestamps and fold-wise predictions are not supplied. Consequently, these files support inspection of the defined positive windows and model settings, not a complete replay of the temporal experiment. Saved interval labels are not independent movement timings.

This package provides evaluation scripts and machine-readable experiment records. Training implementations are not included in this folder; model architecture, processing and selection procedures are described in the manuscript and supplementary methods. Configuration files are records, not a standalone training launcher.

## Data reuse

Refer to the [UpperMyo data repository](https://github.com/HuangheZhang/UpperMyo) for data reuse terms. External datasets retain their providers' terms.
