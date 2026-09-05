# Changelog

What changed between releases, and what it means for a caller. Versions follow
[semantic versioning](https://semver.org): the answer a ZIP resolves to is part
of the API, so a table regeneration that *moves* a ZIP between zones is a minor
bump at least, not a patch.

The version is written in `ziptz.go`, `ziptz.py` and `pyproject.toml`, and
`make parity` refuses to build if the three disagree.

## Unreleased

Nothing yet.

## 0.1.0

First release, and the first as a module of its own — the library was extracted
from the [clock](https://github.com/choey/clock) repository it grew up in, and
its import path changed with it:

```
github.com/choey/clock/ziptz   ->   github.com/choey/ziptz
```

On PyPI the distribution is **`ziptz-us`**, while the module is still `ziptz`.
The bare name is held by a 2013-era registration with no files attached, so
`pip install ziptz` fails for everyone and only PEP 541 could free it; `-us` is
in any case an accurate thing to call a library that resolves US ZIP codes and
nothing else. Nobody's `import ziptz` changes.

Nothing else changed in the split; the tables, the answers and the error texts
are the ones the clock had been using.

What it does, for a first reader:

- `Zone`/`zone` — a 3- or 5-digit US ZIP to an IANA name, from about 1.3 KB of
  tables compiled into the source. No dependencies, no data files, no network.
- `Location`/`location`, `Abbrev`/`abbrev`, `Generic`/`generic` — the same
  answer as a loaded zone, as the abbreviation at an instant, and as the
  daylight-saving-agnostic short name.
- `PrefixZone`/`prefix_zone` and `ExactZone`/`exact_zone` — the two table
  lookups the above are composed from, for callers who want to know which one
  answered.

Accuracy: five digits are exact; three digits give the majority zone for that
prefix, right for 33,558 of 33,791 ZIPs and wrong for the 233 that sit on the
losing side of a boundary their prefix has to round across. PO-box and
single-building ZIPs have no delivery area in the source data and fall back to
their prefix even when given in full.

The Go and Python implementations are held to the same answers by a sweep of
all 101,000 tokens on every build, not by inspection.
