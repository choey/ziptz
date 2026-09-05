.PHONY: test test-go test-py parity sweep regen

test: test-go test-py parity sweep

test-go:
	go test ./...

test-py:
	python3 -m unittest -q test_ziptz

# What the two suites cannot check, because each reads only its own language:
# that the generated literals are the same text, and that the version is the
# same number in all three places it is written down.
#
# genzips.py writes both literals in one pass, so they can only differ if
# someone edited one by hand -- exactly the edit the header on each of them
# forbids, and one a passing test suite would not notice.
#
# The version is the more likely drift and the worse one. It is declared in
# ziptz.go, in ziptz.py and in pyproject.toml, and after release it is also a
# git tag and a PyPI filename; a bump that misses one of the three ships a Go
# module and a wheel that disagree about what they are, publicly and
# permanently.
parity:
	@go_runs=$$(sed -n 's/^const runs = "\(.*\)".*/\1/p' ziptz.go); \
	py_runs=$$(sed -n 's/^RUNS = "\(.*\)".*/\1/p' ziptz.py); \
	go_exc=$$(sed -n 's/^const exceptions = "\(.*\)".*/\1/p' ziptz.go); \
	py_exc=$$(sed -n 's/^EXCEPTIONS = "\(.*\)".*/\1/p' ziptz.py); \
	if [ -z "$$go_runs" ] || [ -z "$$py_runs" ]; then \
		echo "parity: could not find the run tables -- did a literal get renamed?"; exit 1; \
	fi; \
	if [ "$$go_runs" != "$$py_runs" ]; then \
		echo "parity: the run tables differ between ziptz.go and ziptz.py"; exit 1; \
	fi; \
	if [ "$$go_exc" != "$$py_exc" ]; then \
		echo "parity: the exception tables differ between ziptz.go and ziptz.py"; exit 1; \
	fi; \
	go_ver=$$(sed -n 's/^const Version = "\(.*\)".*/\1/p' ziptz.go); \
	py_ver=$$(sed -n 's/^__version__ = "\(.*\)".*/\1/p' ziptz.py); \
	toml_ver=$$(sed -n 's/^version = "\(.*\)".*/\1/p' pyproject.toml); \
	if [ -z "$$go_ver" ] || [ -z "$$py_ver" ] || [ -z "$$toml_ver" ]; then \
		echo "parity: could not find all three versions -- did a declaration get renamed?"; \
		echo "  ziptz.go '$$go_ver'  ziptz.py '$$py_ver'  pyproject.toml '$$toml_ver'"; exit 1; \
	fi; \
	if [ "$$go_ver" != "$$py_ver" ] || [ "$$go_ver" != "$$toml_ver" ]; then \
		echo "parity: the version is written three times and they disagree:"; \
		echo "  ziptz.go        $$go_ver"; \
		echo "  ziptz.py        $$py_ver"; \
		echo "  pyproject.toml  $$toml_ver"; exit 1; \
	fi; \
	echo "parity: $$(($${#go_runs} / 4)) range records and $${#go_exc} characters of exceptions, identical in both; version $$go_ver in all three places"

# Every ZIP there is, through both libraries, compared. The tests above cover
# the cases someone thought of; this covers the ones nobody did -- all 1,000
# prefixes and all 100,000 five-digit codes, answers and error text alike.
sweep:
	@out=$${TMPDIR:-/tmp}/ziptz-sweep.$$$$; mkdir -p $$out; \
	go run tools/sweep.go >$$out/go && python3 tools/sweep.py >$$out/py && \
	if cmp -s $$out/go $$out/py; then \
		echo "sweep: $$(wc -l <$$out/go | tr -d ' ') answers, identical"; \
	else \
		echo "sweep: the two libraries disagree:"; diff $$out/py $$out/go | head -20; \
		rm -rf $$out; exit 1; \
	fi; rm -rf $$out

# Rewrites the tables in ziptz.go and ziptz.py from Census data -- see
# "Regenerating" in README.md, and expect to need it almost never. Needs
# timezonefinder, which nothing else here does:
#
#     python3 -m venv .venv && .venv/bin/pip install timezonefinder
#     .venv/bin/python tools/genzips.py
regen:
	tools/genzips.py
