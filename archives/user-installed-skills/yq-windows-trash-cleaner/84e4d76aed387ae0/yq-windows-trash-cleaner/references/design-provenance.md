# Design provenance

The whole-disk report structure and three-tier human decision model were inspired by `storage-analyzer` from `KKKKhazix/khazix-skills` at commit `2b4a645cfdc894156ae347d897723562f719ce95`, licensed MIT, Copyright (c) 2026 数字生命卡兹克.

Source: https://github.com/KKKKhazix/khazix-skills/tree/2b4a645cfdc894156ae347d897723562f719ce95/storage-analyzer

This skill independently implements the Windows workflow. No upstream Python, HTML, CSS, JavaScript, or assets are copied. The adopted ideas are:

- separate machine-readable scan data from human analysis;
- show volume overview, top consumers, priority, classification, and prevention;
- use a simple three-tier decision model;
- surface access failures and estimated reclaim uncertainty;
- keep destructive actions behind a separate authorization boundary.

The upstream Windows scanner and delete server are not bundled because the reviewed version states Windows is not real-machine tested and its direct/batch deletion model lacks this skill's Git, process, manifest, drift, backup, and action-log gates.
