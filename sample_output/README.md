# Sample output

The committed seed brief is the offline pipeline run against
`fixtures/germany_head_of_operations.json`:

- [Germany_Head_of_Operations.md](Germany_Head_of_Operations.md)
- [Germany_Head_of_Operations.json](Germany_Head_of_Operations.json)

Re-generate:

```bash
python -m src.pipeline --offline --role "Head of Operations" --market "Germany"
```

Dated live runs (`Germany_Head_of_Operations_YYYY-MM-DD.*`) are gitignored.
Every quantitative claim in the seed is sourced; the one Head of Operations
pay band tagged **(SYNTHETIC)** is a control, not a finding.
