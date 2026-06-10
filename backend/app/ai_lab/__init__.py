"""AI Lab (premium / beta) — Phase 10. NOT implemented now.

Scope (future): pilling, weave-defect detection, rouloté control, crocking-risk
estimation, fixation/steaming index, 60fps edge video, ONNX/CoreML export.

Hard prerequisites before any of this ships (see HANDOFF risks):
  * real labelled datasets (no dataset => no model);
  * training pipeline + model versioning/lineage (``model_versions`` table);
  * AI Act governance: human-in-the-loop, decision logging, override capability,
    documented metrics and validation (``validation_runs`` table).

Sold as beta / Enterprise only. Never presented as an autonomous replacement of
the quality manager."""
