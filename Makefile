.PHONY: test test-go test-py parity sweep regen

test: test-go test-py parity sweep

test-go:
	go test ./...

test-py:
	python3 -m unittest -q test_ziptz

# What neither suite can check, because each reads only its own language: the
# generated tables, the hand-written ZONES and GENERIC tables, and the version
# in its three places. See the header of the script.
parity:
	@tools/parity.sh $(V)

# Rewrites the tables in ziptz.go and ziptz.py from Census data -- see
# "Regenerating" in README.md, and expect to need it almost never. Needs
# timezonefinder, which nothing else here does:
#
#     python3 -m venv .venv && .venv/bin/pip install timezonefinder
#     .venv/bin/python tools/genzips.py
regen:
	tools/genzips.py
