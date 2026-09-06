"""Tests for ziptz, run against the same data as ziptz_test.go.

    python3 -m unittest -q test_ziptz     # or: make test-py

Everything both suites check lives in testdata/cases.json: the ZIP cases, the
zones, the figures the generated tables should hold, and -- in "checks" -- the
names of the properties each suite has to implement. A name in that list with
no test behind it here fails, so this suite cannot quietly cover less than the
Go one, which reads the same file and answers to the same names.

Add a case or a check there rather than here.
"""

import datetime
import importlib.util
import json
import pathlib
import sys
import unittest

import ziptz

# The text a case's error kind must carry.
ERROR_KINDS = {
    "malformed": "not a US ZIP code",
    "unassigned": "no US time zone is recorded",
}


def load():
    path = pathlib.Path(__file__).resolve().parent / "testdata" / "cases.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data["cases"]
    # A truncated or renamed file would otherwise pass as zero cases run.
    assert len(cases) >= 50, f"only {len(cases)} cases in {path}; it looks truncated"
    for case in cases:
        assert ("zone" in case) != ("error" in case), (
            f"case {case['token']!r} must have exactly one of zone and error"
        )
        assert case.get("error", "malformed") in ERROR_KINDS, (
            f"case {case['token']!r} has unknown error kind {case['error']!r}"
        )
    data["instants"] = {
        name: datetime.datetime.strptime(when, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc
        )
        for name, when in data["instants"].items()
    }
    return data


DATA = load()
CASES = DATA["cases"]
ZONE_CASES = DATA["zones"]
TABLES = DATA["tables"]
WINTER, SUMMER = DATA["instants"]["winter"], DATA["instants"]["summer"]


def exception_groups():
    """Every (prefix, letter, count, suffixes) the exception table records."""
    i = 0
    while i < len(ziptz.EXCEPTIONS):
        prefix = ziptz.EXCEPTIONS[i : i + 3]
        letter = ziptz.EXCEPTIONS[i + 3]
        count = int(ziptz.EXCEPTIONS[i + 4 : i + 6])
        body = i + 6
        yield prefix, letter, count, [
            ziptz.EXCEPTIONS[body + k * 2 : body + k * 2 + 2] for k in range(count)
        ]
        i = body + count * 2


def run_records():
    """Every (prefix, letter) in the run table."""
    return [
        (ziptz.RUNS[i : i + 3], ziptz.RUNS[i + 3])
        for i in range(0, len(ziptz.RUNS), 4)
    ]


class Checks(unittest.TestCase):
    """One method per name in the shared "checks" list.

    The mapping at the bottom of this class is what ties them together, and
    what test_every_declared_check_is_implemented holds to the file.
    """

    def zone_cases(self):
        for case in CASES:
            token, why = case["token"], case["why"]
            with self.subTest(token=token, why=why):
                if "zone" in case:
                    self.assertEqual(ziptz.zone(token), case["zone"], why)
                    continue
                with self.assertRaises(ziptz.ZipError) as caught:
                    ziptz.zone(token)
                self.assertIn(ERROR_KINDS[case["error"]], str(caught.exception), why)

    def location_cases(self):
        """location() has to agree with zone() on every case, and fail on the
        same ones: the clock calls it, not zone()."""
        for case in CASES:
            token = case["token"]
            with self.subTest(token=token, why=case["why"]):
                if "zone" not in case:
                    with self.assertRaises(ziptz.ZipError):
                        ziptz.location(token)
                    continue
                try:
                    self.assertEqual(ziptz.location(token).key, case["zone"])
                except ziptz.ZipError as exc:
                    # A system without this zone installed is an environment
                    # fact, not a bug in the table.
                    if "time zone database lacks" not in str(exc):
                        raise
                    self.skipTest(f"this system's tz database lacks {case['zone']}")

    def abbrev_cases(self):
        for case in ZONE_CASES:
            for season, at in (("winter", WINTER), ("summer", SUMMER)):
                with self.subTest(zone=case["zone"], season=season, why=case["why"]):
                    try:
                        got = ziptz.abbrev(case["token"], at)
                    except ziptz.ZipError as exc:
                        if "time zone database lacks" not in str(exc):
                            raise
                        self.skipTest(f"this system's tz database lacks {case['zone']}")
                    self.assertEqual(got, case[season], case["why"])

    def generic_cases(self):
        for case in ZONE_CASES:
            with self.subTest(zone=case["zone"], why=case["why"]):
                self.assertEqual(ziptz.generic(case["token"]), case["generic"], case["why"])

    def abbrev_and_generic_refuse_what_zone_refuses(self):
        for case in CASES:
            if "error" not in case:
                continue
            with self.subTest(token=case["token"], why=case["why"]):
                want = ERROR_KINDS[case["error"]]
                with self.assertRaises(ziptz.ZipError) as caught:
                    ziptz.abbrev(case["token"], SUMMER)
                self.assertIn(want, str(caught.exception))
                with self.assertRaises(ziptz.ZipError) as caught:
                    ziptz.generic(case["token"])
                self.assertIn(want, str(caught.exception))

    def table_figures(self):
        """What the generated tables hold, against what the data says they
        should. Regenerating changes these, which is the point: the new figures
        have to be written down before the suite goes green again."""
        runs = run_records()
        groups = list(exception_groups())
        self.assertEqual(len(runs), TABLES["runs"])
        self.assertEqual(sum(1 for _, letter in runs if letter != "-"), TABLES["runs_named"])
        self.assertEqual(sum(count for _, _, count, _ in groups), TABLES["exceptions"])
        self.assertEqual(len(groups), TABLES["exception_prefixes"])
        self.assertEqual(len(ziptz.ZONES), TABLES["letters"])
        self.assertEqual(len(ziptz.GENERIC), TABLES["generics"])
        self.assertEqual(
            sum(1 for n in range(1000) if ziptz.prefix_zone(f"{n:03d}")),
            TABLES["assigned_prefixes"],
        )

    def runs_ascending(self):
        self.assertEqual(len(ziptz.RUNS) % 4, 0)
        prev = ""
        for prefix, _ in run_records():
            self.assertGreater(prefix, prev)
            prev = prefix

    def runs_letters_known(self):
        for prefix, letter in run_records():
            if letter != "-":
                self.assertIn(letter, ziptz.ZONES, prefix)
        for _, letter, _, _ in exception_groups():
            self.assertIn(letter, ziptz.ZONES)

    def exceptions_ascending(self):
        prev = ""
        for prefix, _, count, suffixes in exception_groups():
            self.assertGreaterEqual(prefix, prev)
            prev = prefix
            self.assertGreater(count, 0)
            self.assertEqual(suffixes, sorted(suffixes))
            self.assertEqual(len(set(suffixes)), len(suffixes))

    def exceptions_beat_their_prefix(self):
        """A five-digit ZIP is exact, so every listed exception must win over
        its own prefix -- and must actually disagree with it, or it would not
        be one."""
        for prefix, letter, _, suffixes in exception_groups():
            for suffix in suffixes:
                zip_code = prefix + suffix
                with self.subTest(zip=zip_code):
                    self.assertEqual(ziptz.zone(zip_code), ziptz.ZONES[letter])
                    self.assertNotEqual(ziptz.zone(zip_code), ziptz.prefix_zone(prefix))

    def every_zone_has_a_case(self):
        self.assertEqual(
            {case["zone"] for case in ZONE_CASES}, set(ziptz.ZONES.values())
        )

    def generic_covers_every_zone(self):
        self.assertEqual(set(ziptz.GENERIC), set(ziptz.ZONES.values()))

    def non_shifting_zones_are_their_own_generic(self):
        """A zone that never shifts has no pair to generalise over, so its
        generic name has to be the one abbreviation it ever uses."""
        for case in ZONE_CASES:
            if case["winter"] == case["summer"]:
                with self.subTest(zone=case["zone"]):
                    self.assertEqual(case["generic"], case["winter"])

    def the_index_matches_the_tables(self):
        """The dicts the first lookup builds must answer exactly what walking
        the tables by hand answers.

        This is the newest machinery here and the only part with a second
        representation of the same data: RUNS and EXCEPTIONS ship, and the
        index is derived from them once, at runtime. Every other check reads
        the derived answer, so a build that dropped a group or mis-sliced a
        suffix would look correct to all of them. This walks the strings
        independently -- through the same helpers that check the tables are
        well formed -- and holds the lookups to that.
        """
        for prefix, letter, _, suffixes in exception_groups():
            zone_name = ziptz.ZONES[letter]
            for suffix in suffixes:
                with self.subTest(zip=prefix + suffix):
                    self.assertEqual(ziptz.exact_zone(prefix + suffix), zone_name)

        # and nothing the table does not name
        listed = {p + s for p, _, _, ss in exception_groups() for s in ss}
        self.assertEqual(len(listed), TABLES["exceptions"])
        for n in range(0, 100000, 977):  # a stride, not all 100,000: the sweep does those
            token = f"{n:05d}"
            if token not in listed:
                with self.subTest(zip=token):
                    self.assertEqual(ziptz.exact_zone(token), "")

        # the run table, expanded the long way: a record's zone reaches to the
        # next record's prefix, and the last one to 999
        records = run_records()
        for i, (start, letter) in enumerate(records):
            end = records[i + 1][0] if i + 1 < len(records) else "999"
            stop = 1000 if end == "999" and i + 1 == len(records) else int(end)
            for n in range(int(start), stop):
                with self.subTest(prefix=f"{n:03d}"):
                    self.assertEqual(
                        ziptz.prefix_zone(f"{n:03d}"), ziptz.ZONES.get(letter, ""))

    def errors_quote_a_bounded_token(self):
        """An error is written to be printed as-is, which means it can land in
        a log line, so the token it quotes has to be bounded and printable.

        100,000 digits made a 100,065-character error, and a newline made an
        error that was two log lines with the second one attacker-written.
        bytes is here too: it has a length, isascii() and isdigit(), so it
        passed every check and then missed both indexes, and the caller was
        told San Francisco's prefix does not exist.
        """
        for name, token in (
            ("very long", "9" * 100000),
            ("newline", "941\nCRITICAL not really"),
            ("ansi", "941\x1b[31m"),
            ("astral", "941\U0001F4A9x"),
            ("bytes", b"94110"),
        ):
            with self.subTest(token=name):
                with self.assertRaises(ziptz.ZipError) as caught:
                    ziptz.zone(token)
                msg = str(caught.exception)
                self.assertIn("is not a US ZIP code", msg)
                self.assertLessEqual(
                    len(msg), 120, "the error must not echo the token whole")
                self.assertTrue(
                    all(" " <= c <= "~" for c in msg),
                    "the error must be printable ASCII")
        # and a short one is still quoted whole rather than trimmed
        with self.assertRaises(ziptz.ZipError) as caught:
            ziptz.zone("9411")
        self.assertIn('"9411"', str(caught.exception))

    def prefix_zone_wants_three_digits(self):
        """A prefix is three digits or it is nothing.

        The binary search underneath finds the last record sorting at or below
        its argument, which for a shorter or longer string still finds one --
        "99" sorts below "990", "9999" above "995" -- so without a length check
        each answers a zone for a question nobody asked. This side had no such
        check for a while and the two ports disagreed here, in the one place
        the sweep cannot look: every token it asks about is well formed by
        construction.
        """
        for p3 in ("", "9", "99", "9999", "94110", " 94", "94 "):
            with self.subTest(prefix=p3):
                self.assertEqual(
                    ziptz.prefix_zone(p3), "", "only three digits is a prefix")
        self.assertNotEqual(
            ziptz.prefix_zone("941"), "", "the length check went too far")

    # Python only, and named as such in the shared file: Go has no default
    # arguments, and only Python can be imported two ways.
    def abbrev_defaults_to_now(self):
        self.assertEqual(
            ziptz.abbrev("94110"),
            ziptz.abbrev("94110", datetime.datetime.now(datetime.timezone.utc)),
        )

    def package_and_module_agree(self):
        """ziptz imports two ways and both have to answer the same.

        A copy of ziptz.py on its own is a module; the directory around it is a
        package, and __init__.py hands through to the module. Only the package
        form goes into a wheel, so a name the hand-off forgets is invisible
        everywhere except an installed copy -- which is exactly how GENERIC
        went missing from it once.
        """
        here = pathlib.Path(__file__).resolve().parent
        spec = importlib.util.spec_from_file_location("_ziptz_mod", here / "ziptz.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # A package, not a module: the search location is what lets its
        # `from .ziptz import ...` resolve, and it has to be in sys.modules
        # before exec for the relative import to find its parent.
        spec = importlib.util.spec_from_file_location(
            "_ziptz_pkg", here / "__init__.py", submodule_search_locations=[str(here)]
        )
        package = importlib.util.module_from_spec(spec)
        sys.modules["_ziptz_pkg"] = package
        try:
            spec.loader.exec_module(package)
        finally:
            del sys.modules["_ziptz_pkg"]

        wanted = (
            set(module.__all__)
            | {name for name in vars(module) if name.isupper()}
            | {"__version__"}
        )
        missing = sorted(name for name in wanted if not hasattr(package, name))
        self.assertEqual(missing, [], "names __init__.py does not hand through")
        for case in CASES:
            if "zone" in case:
                self.assertEqual(module.zone(case["token"]), package.zone(case["token"]))

    # name in testdata/cases.json -> the method above that answers to it
    IMPLEMENTED = {
        "zone-cases": zone_cases,
        "location-cases": location_cases,
        "abbrev-cases": abbrev_cases,
        "generic-cases": generic_cases,
        "abbrev-and-generic-refuse-what-zone-refuses": abbrev_and_generic_refuse_what_zone_refuses,
        "table-figures": table_figures,
        "runs-ascending": runs_ascending,
        "runs-letters-known": runs_letters_known,
        "exceptions-ascending": exceptions_ascending,
        "exceptions-beat-their-prefix": exceptions_beat_their_prefix,
        "every-zone-has-a-case": every_zone_has_a_case,
        "generic-covers-every-zone": generic_covers_every_zone,
        "non-shifting-zones-are-their-own-generic": non_shifting_zones_are_their_own_generic,
        "prefix-zone-wants-three-digits": prefix_zone_wants_three_digits,
        "the-index-matches-the-tables": the_index_matches_the_tables,
        "errors-quote-a-bounded-token": errors_quote_a_bounded_token,
        "abbrev-defaults-to-now": abbrev_defaults_to_now,
        "package-and-module-agree": package_and_module_agree,
    }

    def test_every_declared_check_runs(self):
        for name in DATA["checks"] + DATA["language_only"]["python"]:
            with self.subTest(check=name):
                self.assertIn(
                    name, self.IMPLEMENTED,
                    f"testdata/cases.json asks for {name!r} and this suite has no test for it",
                )
                self.IMPLEMENTED[name](self)

    def test_nothing_is_tested_that_is_not_declared(self):
        """The other direction: a check here and not in the file is a check the
        Go suite was never asked for."""
        declared = set(DATA["checks"]) | set(
            name for names in DATA["language_only"].values() for name in names
        )
        self.assertEqual(sorted(set(self.IMPLEMENTED) - declared), [])


if __name__ == "__main__":
    unittest.main()
