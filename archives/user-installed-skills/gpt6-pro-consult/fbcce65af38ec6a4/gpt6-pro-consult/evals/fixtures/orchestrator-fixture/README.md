# Pricing Fixture

`apply_discount` must reject percentages outside 0–100 and must not silently produce a negative total. The current implementation lacks that validation. Run:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

During eval, copy this directory to the isolated run workspace before editing it.
