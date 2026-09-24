# A graph is a view of evidence

!!! abstract "TL;DR"

    The picture helps navigate an assessment. It does not strengthen the evidence, verify
    report freshness or turn a suspect into a failed item. Filters change only the view.

## Two directions, one relationship

A test declares `verifies REQ-SVC-01`, so its arrow points to the requirement. Asking what
changes downstream of the requirement follows that arrow in reverse. qmstrace highlights
this forward reach while retaining the authored arrow and label. Direct test-to-requirement
links need not pass through design or code; cycles are allowed in the display.

## Several properties can coexist

An item can be frozen, changed, withdrawn and suspect at once. Type colors answer what kind
of item it is; separate text badges describe those properties. A suspect is a review
obligation. It does not assert that the item is outdated or that its tests fail.

Current edges alone cannot explain every suspect. A removed historical link may still make
an existing dependant suspect. The finding inspector therefore gives each root, governing
baseline, graph version and distance. It does not overlay historical edges onto today's
network: such a combined picture could imply a path that never existed in either tree.

## A snapshot has boundaries

Python computes the assessment and reach once. The file embeds those values and the browser
assets; selecting, searching or filtering requires no network and performs no new judgment.
Its item list includes visible sibling citations, but their working trees are not pins and
traversal stops at this repo's edge. The evidence panel keeps those limits in view.

A saved file can become stale as soon as source changes. Regenerate it to inspect the new
working tree. Its initial selection and filters do not remove included metadata from the
file. A shareable artifact needs the same review as the text assessment it presents.
