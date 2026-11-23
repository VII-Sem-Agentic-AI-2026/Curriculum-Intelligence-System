import os, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("CIS_GOVERNANCE_DIR", tempfile.mkdtemp(prefix="cis_gov_test_"))
