"""Compatibility exports for deterministic text views; owners contain the implementation."""

from qmstrace.render._evidence import evidence as evidence
from qmstrace.render.text._checks import PROJECT_GAP_HEADING as PROJECT_GAP_HEADING
from qmstrace.render.text._checks import VIOLATION_HEADING as VIOLATION_HEADING
from qmstrace.render.text._checks import check as check
from qmstrace.render.text._checks import ledger_check as ledger_check
from qmstrace.render.text._results import results as results
from qmstrace.render.text._schema import rules as rules
from qmstrace.render.text._schema import schema_copies as schema_copies
from qmstrace.render.text._status import CATEGORY as CATEGORY
from qmstrace.render.text._status import LISTED as LISTED
from qmstrace.render.text._status import TESTED as TESTED
from qmstrace.render.text._status import VERIFY_BY as VERIFY_BY
from qmstrace.render.text._status import status as status
from qmstrace.render.text._walks import impact as impact
from qmstrace.render.text._walks import ledger_impact as ledger_impact
from qmstrace.render.text._walks import ledger_thread as ledger_thread
from qmstrace.render.text._walks import thread as thread
