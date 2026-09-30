# Internal multimodal tasks

These configs and their helpers are vendored from the deployment's
`mm_third_party/FlagEvalMM/internal/tasks/vqa` directory (2026-09-29).
They cover all `paneval/internal/tasks/...` paths in evaluation migration
`0002_auto_20260609_1108.py`, including its two commented-out OCRLite configs.
Vendoring OCRLite does not enable it in the dataset catalog.

Local adaptations use `evalmm` imports and the current prompt template API
(`build_prompt(annotation=...)`). Dataset locations and scoring are preserved.
TDIUC requires `num2words` and `scipy`; `playbooks/conda-envs.yml` includes both
when building the evalmm environment. Existing executor environments must also
have these dependencies before running TDIUC; repacking the archive alone does
not replace an already extracted `/root/miniconda3` environment.

For every evaluation attempt, `run_online` rsyncs `third_party/mm/` to the
pinned executor's `/share/project/mmenv/<batch>.<attempt>/__paneval__/`.
After unpacking (or reusing) the evaluator, `bootstrap.sh` copies this directory
to `__paneval__/paneval/internal/`, preserving relative helper imports such as
TDIUC's `../vqa2.0/vqa_coco_dataset.py`. The public evaluator archive does not
need to contain these internal tasks.

This directory contains code only. Executors still need the images and
annotations mounted at the configs' `data_root` locations, including the legacy
`/share/projset/...` path used by the CV-Bench robustness config. Those paths
must resolve to the intended datasets; copying the task code does not migrate
dataset assets.
