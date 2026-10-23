# Write traced docs with diagrams and tables

!!! abstract "TL;DR"

    Give each requirement and design element a heading that starts with its ID. Everything
    under it, down to the next heading at the same or a higher level, is the item — sub-sections,
    tables and diagrams included. Write its fields and links as `Key: value` lines anywhere in
    that section, never in a table. Tables, diagrams and prose may name IDs; they declare nothing.

## Steps

1. **Start the item's heading with its ID.** A section number before it, bold or backticks
   around it, and a Pandoc attribute after the title are layout, not part of the ID or the
   title:

    ``` markdown
    ### 1.1 REQ-RCH-01 — Registration under a supplied client ID {#req-registration}
    ### 1.2 **REQ-RCH-02** — Only a caller with the key registers
    ### 2.2 `DSN-RCH-02` — Key guard
    ```

    An ID later in the heading — `## Key guard (DSN-RCH-02)` — declares nothing.

2. **Structure the item under its heading as you like.** A deeper heading —
   `#### Acceptance criteria`, `#### Flow` — belongs to the item, and so do its tables and
   diagrams. They are the item's text: after a baseline, editing them is a change like rewording
   the statement. Renumbering the document is not.

3. **Write each field and link as a line in the item's section** — right under the heading, or
   in a sub-section such as `#### Traceability`:

    ``` markdown
    #### 2.1.2 Traceability

    Satisfies: REQ-RCH-01
    ```

    A `Satisfies` cell in a table is not read. Nor is a line outside every item's section.

4. **Name IDs freely in tables, diagrams and prose** — a summary of the requirements, a flow
   between elements. They link nothing. An ID of this repo's kind that nothing declares, later in
   a heading or at the start of a table row, is reported: it was probably meant as a declaration.

5. **Plan test cases the same way, where the project keeps a Test Specification.** A test
   case is a heading with its ID and a `verifies:` line; the automated tests that run it name
   its ID, not the requirement:

    ``` markdown
    ## TC-SVC-01.1 — A call without a valid key is refused
    verifies: REQ-SVC-01
    ```

6. **Check.**

    ``` sh
    qmstrace check --strict
    ```

## A design document written this way

It reads as an architecture guide, and every element in it is declared:

```` markdown
--8<-- "fixtures/mini/rich/docs/design/gateway-design.md"
````

`qmstrace check --strict` in that repo:

``` text
--8<-- "cli/golden/check-rich.txt"
```

## When something is not read

Three slips in the same repo — the link to `REQ-RCH-02` moved into the key guard's table, a
planned `REQ-RCH-03` added to the summary table, and a heading that ends with `(DSN-RCH-03)`:

``` text
--8<-- "cli/golden/check-rich-slips.txt"
```

- **The table row** leaves two gaps, and both name it: the design element satisfies nothing, and
  the requirement has no design element. Write the link as a line in the section.
- **An ID that nothing declares** is `V16`. Declare it as a heading where its kind is read — or,
  if it only names a planned item, take it out of the table until the item exists.

## Check an ID before the first baseline

For an item type listed in a baseline's `covers`, include exactly one configured subject key
as a whole segment between the first and last ID segments. `REQ-SVC-03` identifies subject
`SVC`; `REQ-03` does not. Run `qmstrace check` before cutting the tag. V17 names missing or
ambiguous ownership while it can still be corrected in the current tree:

``` text
--8<-- "cli/golden/check-authoring-v17.txt"
```

If the tag has already frozen a bad ID, `check` exits `2` and names the tag. Correct the
current item, then follow the project's approval process to establish a successor baseline;
do not move the old tag.

!!! note "Not built yet"

    An ID named in prose or inside a diagram is not checked yet: one that exists nowhere passes
    silently. Only the forms above — later in a heading, first in a table row — are reported.
