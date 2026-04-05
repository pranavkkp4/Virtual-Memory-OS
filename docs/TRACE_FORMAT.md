# Trace Format

This project normalizes all trace inputs to the internal event shape:

```text
(timestamp, process_id, page_id, is_write)
```

## Supported Inputs

- CSV traces with headers such as `timestamp, process_id, page_id, is_write`
- CSV traces that provide `address` or `virtual_address` instead of `page_id`
- Legacy positional CSV rows in the form `page_id, process_id, is_write`

## Normalization Rules

- Missing timestamps are synthesized from the input row order.
- Addresses are converted to page numbers with `address // page_size`.
- `is_write` accepts values like `0/1`, `true/false`, `read/write`, and `r/w`.
- Rows are sorted by timestamp after loading.
- Validation rejects negative timestamps, process IDs, and page IDs.

## Example

```csv
timestamp,process_id,address,is_write
0,0,0x00000000,0
1,0,0x00000010,0
2,1,0x00001000,1
```

With a `page_size` of `4096`, this becomes:

```text
(0, 0, 0, False)
(1, 0, 0, False)
(2, 1, 1, True)
```
