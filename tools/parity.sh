#!/bin/sh
# What neither suite can check, because each reads only its own language: that
# the two files say the same thing where they are supposed to.
#
# The generated tables are compared as text, before either library is asked to
# interpret them -- genzips.py writes both in one pass, so they can only differ
# if someone edited one by hand, which is exactly the edit the header on each
# forbids and the one a passing test suite would not notice.
#
# The hand-written tables are compared too. ZONES and GENERIC are maintained by
# a person, one line per entry in the same order on both sides precisely so
# that this can diff them without parsing either.
#
# And the version, which is the more likely drift and the worse one: it is
# declared in ziptz.go, in ziptz.py and in pyproject.toml, and after release it
# is also a git tag and a PyPI filename. A bump that misses one ships a Go
# module and a wheel that disagree about what they are, publicly and
# permanently.
#
# Usage: tools/parity.sh [-v]
set -eu

cd "$(dirname "$0")/.."
verbose=${1:-}
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
fail=0

same() {
	what=$1 a=$2 b=$3 note=$4
	if [ -z "$a" ]; then
		echo "FAIL $what: found nothing in ziptz.go -- did a declaration get renamed?"
		fail=1
	elif [ "$a" = "$b" ]; then
		[ -z "$verbose" ] || printf 'ok   %s (%s)\n' "$what" "$note"
	else
		echo "FAIL $what differs between ziptz.go and ziptz.py"
		fail=1
	fi
}

go_runs=$(sed -n 's/^const runs = "\(.*\)".*/\1/p' ziptz.go)
py_runs=$(sed -n 's/^RUNS = "\(.*\)".*/\1/p' ziptz.py)
same "the run table" "$go_runs" "$py_runs" "$((${#go_runs} / 4)) records"

# Characters, not records: the exception table is variable-stride -- a group is
# a prefix, a letter, a count, then that many two-digit suffixes -- so there is
# no divisor that turns its length into a record count.
go_exc=$(sed -n 's/^const exceptions = "\(.*\)".*/\1/p' ziptz.go)
py_exc=$(sed -n 's/^EXCEPTIONS = "\(.*\)".*/\1/p' ziptz.py)
same "the exception table" "$go_exc" "$py_exc" "${#go_exc} characters"

sed -n "s/^	'\(.\)': \"\([A-Za-z_/]*\)\",\$/\1=\2/p" ziptz.go >"$out/go.zones"
sed -n 's/^    "\(.\)": "\([A-Za-z_/]*\)",$/\1=\2/p' ziptz.py >"$out/py.zones"
same "the letter table" "$(cat "$out/go.zones")" "$(cat "$out/py.zones")" \
	"$(wc -l <"$out/go.zones" | tr -d ' ') entries"

sed -n 's|^	"\([A-Za-z_/]*\)": *"\([A-Za-z]*\)",$|\1=\2|p' ziptz.go >"$out/go.generic"
sed -n 's|^    "\([A-Za-z_/]*\)": "\([A-Za-z]*\)",$|\1=\2|p' ziptz.py >"$out/py.generic"
same "the generic name table" "$(cat "$out/go.generic")" "$(cat "$out/py.generic")" \
	"$(wc -l <"$out/go.generic" | tr -d ' ') entries"

go_ver=$(sed -n 's/^const Version = "\(.*\)"$/\1/p' ziptz.go)
py_ver=$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' ziptz.py)
toml_ver=$(sed -n 's/^version = "\(.*\)"$/\1/p' pyproject.toml)
if [ -z "$go_ver" ] || [ "$go_ver" != "$py_ver" ] || [ "$go_ver" != "$toml_ver" ]; then
	echo "FAIL the version is written three times and they disagree:"
	echo "     ziptz.go '$go_ver'  ziptz.py '$py_ver'  pyproject.toml '$toml_ver'"
	fail=1
else
	[ -z "$verbose" ] || printf 'ok   the version (%s in all three places)\n' "$go_ver"
fi

[ "$fail" = 0 ] || exit 1
printf 'parity: tables and version identical in both, version %s\n' "$go_ver"
