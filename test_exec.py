"""Standalone smoke test for utils.py — no external packages needed."""
import sys
import utils

errors = []

# dummySum
result = utils.dummySum(1, 2)
if result != 3:
    errors.append(f"dummySum(1,2) returned {result!r}, expected 3")

# getUrl
url = utils.getUrl("testFiles/testDictionary.txt")
if url != "https://dummy.com/lala?123/":
    errors.append(f"getUrl returned {url!r}")

# getKeywords
kw = utils.getKeywords("testFiles/testDictionary.txt")
if kw != ["devops", "dev ops"]:
    errors.append(f"getKeywords returned {kw!r}")

# getExcludeList
excl = utils.getExcludeList("testFiles/testExcluded.txt", 1, 0)
if excl != ["name1", "namename2"]:
    errors.append(f"getExcludeList returned {excl!r}")

if errors:
    for e in errors:
        print("FAIL:", e, file=sys.stderr)
    sys.exit(1)

print("OK  all utils checks passed")
