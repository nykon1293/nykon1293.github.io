# nykon1293.github.io

Personal website hosted with GitHub Pages.

## Use cases library

The pages under `use-cases/` are generated. The source of truth is one data file, `data/use-cases.json`.

To add one entry:

1. Edit `data/use-cases.json` and add an object. Copy an existing entry and keep these fields: `slug`, `title`, `category`, `summary`, `problem`, `what_si_does`, `setup`, `human_checks`, `examples` (each with `business_type` and `scenario`), `copy_prompt`, `tools_examples`, `effect`, and `caution` (a string, or `null` if there is nothing extra to flag).
2. Use a category name that already appears in the file so the entry lands in that section. `slug` is lowercase words separated by hyphens, and it becomes the URL `/use-cases/<slug>/`.
3. From the repo root, run `python3 scripts/build_use_cases.py`.
4. Commit `data/use-cases.json`, the generated HTML, `use-cases/search.json`, and the sitemap update.

The script writes static HTML plus a lazy-loaded search index. GitHub Pages serves those files as they are. Say SI in new copy. The library intro is the one place that says “formerly called AI.” Examples are illustrations, not client results.
