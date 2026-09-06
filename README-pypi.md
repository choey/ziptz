# ziptz

US ZIP code to IANA time zone, from about 1.3 KB of tables. No dependencies, no
data files, no network: the tables are string constants in the source, and the
first lookup unpacks them into a dict, so a lookup is a hash.

```sh
pip install ziptz-us          # the module is ziptz
```

```python
>>> import ziptz
>>> ziptz.zone("94110")
'America/Los_Angeles'
>>> ziptz.location("10001")
zoneinfo.ZoneInfo(key='America/New_York')
>>> ziptz.abbrev("94110")      # at an instant you pass, or now
'PDT'
>>> ziptz.generic("94110")     # the same zone, daylight saving left out
'PT'
```

The distribution is `ziptz-us` and the module is `ziptz`, the same split as
`python-dateutil` and `dateutil`: the bare name on PyPI is a 2013 registration
with no files attached, and `-us` is in any case accurate for something that
resolves US ZIP codes and nothing else.

## Accuracy

Five digits are exact. Three — the prefix alone — give the majority zone for
that prefix, right for 33,558 of the 33,791 ZIP codes and wrong for the 233
that sit on the losing side of a boundary their prefix has to round across.

```python
ziptz.zone("79835")   # America/Denver  — Canutillo, TX; five digits are exact
ziptz.zone("798")     # America/Chicago — the prefix rounds to the majority
```

It covers the places a US-only table usually forgets — Puerto Rico, the Virgin
Islands, Guam, the Northern Marianas, American Samoa — and it answers a 3-digit
prefix on its own, which is what you have when an address is half filled in.

Three things to know before depending on it:

- **It is not a ZIP validator.** A five-digit code with an assigned prefix
  always gets an answer, whether or not the Postal Service ever issued it. An
  error means "no such prefix", never "no such ZIP".
- **Zone names are coarser than the tz database's.** About 34 IANA zones fold
  onto the 11 that agree with them today, so a ZIP in Knox County, Indiana
  answers `America/New_York` rather than `America/Indiana/Knox`. The clock is
  right; the name is less specific.
- **PO-box and single-building ZIPs** have no delivery area in the source data
  and fall back to their prefix. Where a whole prefix is nothing but those,
  there is nothing to fall back to and the lookup is an error — `00501`
  (Holtsville, NY) is the named case.

The tables carry today's zone *names*, not today's offsets. Daylight saving
comes from whatever tzdata the machine has, so a rule change needs no release
here — and the tables are wrong for historical dates, since several places have
changed zone and these record only where each ZIP is now.

Typed, ships `py.typed`, and supports Python 3.9 and up. Every answer is
checked against a second independent implementation of the same tables — all
101,000 tokens, on every build — so "the two agree" is a build step rather than
a claim.

MIT licensed. The tables derive from US Census ZCTA centroids (public domain)
resolved through [timezone-boundary-builder](
https://github.com/evansiroky/timezone-boundary-builder) (ODbL); the `NOTICE`
file shipped in this distribution carries that attribution and should travel
with any copy.

Full documentation, the accuracy notes in depth, and the source:
**https://github.com/choey/ziptz**
