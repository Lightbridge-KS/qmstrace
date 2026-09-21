# A first look

!!! abstract "TL;DR"

    In five minutes: get qmstrace, run `qmstrace status` on the small example project that comes
    with it, and learn what each block of the output tells you. You need Git and
    [uv](https://docs.astral.sh/uv/).

## Get qmstrace

Until its first release, qmstrace runs from a clone of its repository. uv fetches the right
Python and everything else on the first run.

``` sh
git clone https://github.com/Lightbridge-KS/qmstrace.git
cd qmstrace
```

!!! note "Not public yet"

    The repository becomes public with the first release. Until then, this step needs access
    to it.

## Meet the example project

qmstrace's own tests read a miniature project in `tests/fixtures/mini/`. It has what a real
project has: a **ledger repo** holding the agreement and the project's rules, and two **product
repos**, `service` and `client`, holding requirements, design, code and tests.

In a product repo, every link is written at its downstream end — the test names the requirement
it verifies; the requirement names the agreement clause it comes from:

``` mermaid
flowchart RL
  req["REQ-SVC-01 · requirement<br/>A call carries a key"] -- Origin --> agr["AGR-1 · agreement clause"]
  dsn["DSN-SVC-01 · design element<br/>Key check"] -- Satisfies --> req
  mod["src/service/keys.py · component"] -- Implements --> dsn
  test["test_a_call_without_a_valid_key_is_refused · test case"] -- verifies --> req
```

Each arrow is a line in a file you already write: a field under a requirement's heading, a line
under a design section, a sentence in a module's docstring, a marker on a test.

## Run it

``` sh
uv run qmstrace -C tests/fixtures/mini/service status
```

`-C` runs qmstrace as if it had been started in that folder. Inside a product repo of your own
you would leave it out: qmstrace walks up to the nearest `qmstrace.toml`.

``` text
--8<-- "cli/golden/status-service.txt"
```

## Read it, block by block

1. **`schema:`** — where the rules come from. Here: the project's trace schema, read by path
   from the ledger repo beside this one, plus this repo's own `qmstrace.toml`.
2. **`scanned`** — what was read, per item type. Three requirements in one file, two design
   elements, two modules — one file was ignored, and the line says by which pattern — and four
   test cases. A parametrised test function is one test case, however many times it runs. The
   parenthesis says that the working tree was read, not a pinned commit.
3. **`links:`** — fourteen links entered the graph. A link the rules do not allow never does:
   it becomes a finding instead.
4. **`external AGR-*`** — every agreement clause a requirement cites was checked against the
   agreement: it declares three.
5. **`sibling client`** — the project's other product repo, read from beside this one so that
   its items can be cited by ID. *Not pinned*: it is whatever is checked out there right now.
6. **`baselines:`** — the project declares two kinds of baseline. Judging them is not built yet.
7. **One line per requirement** — its category, the clause it comes from, and what hangs off
   it: design elements, and test cases by level.
8. **`verified by inspection`** — `REQ-SVC-03` has no test to show, by design. It is listed
   apart, because nothing records the inspection yet.
9. **`categories with no requirement here`** — a prompt, not a failure: has each quality been
   considered?
10. **The last line** — nothing is wrong in this repo's trace data, and one coverage rule is not
    met yet: `REQ-SVC-03` has no design element. A gap is work left to do, not an error.

## Check it

``` sh
uv run qmstrace -C tests/fixtures/mini/service check
```

`check` lists that gap with its next move — what to write, and where. How to work through such a
list: [Check your work before you commit](../how-to/check-your-work.md).

## Next

- Every block, and the pipeline's version of this output: [`qmstrace status`](../reference/commands/status.md).
- What *not pinned* and *not verified here* mean, and why they do not fail: [Around the repo](../explanation/around-the-repo.md).
