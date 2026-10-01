"""Run all tests and output JSON for the web page."""
import sys, os, json, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_all():
    started = time.time()
    results = []
    # Import test modules
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tests'))
    for mod_name in ['test_counter', 'test_classify', 'test_db']:
        mod = __import__(mod_name)
        tests = [(k, v) for k, v in sorted(vars(mod).items()) if k.startswith('test_')]
        for name, fn in tests:
            try:
                fn()
                results.append({"title": f"{mod_name}: {name}", "pass": True})
            except Exception as e:
                results.append({"title": f"{mod_name}: {name}", "pass": False, "detail": str(e)})
    ms = int((time.time() - started) * 1000)
    passed = sum(1 for r in results if r["pass"])
    return {"passed": passed, "total": len(results), "ms": ms, "results": results}

if __name__ == "__main__":
    out = run_all()
    if "--json" in sys.argv:
        print(json.dumps(out))
    else:
        for r in out["results"]:
            print(f"{'PASS' if r['pass'] else 'FAIL'}  {r['title']}")
        print(f"\n{out['passed']}/{out['total']} in {out['ms']} ms")
    sys.exit(0 if out["passed"] == out["total"] else 1)
