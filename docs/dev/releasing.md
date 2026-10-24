---
summary: How a qmstrace release is cut — the version lives in pyproject.toml, an annotated vX.Y.Z tag is the one human act, the release workflow gates the tag and drafts a GitHub release from the CHANGELOG with the wheel, a maintainer publishes it, and main moves on to the next .dev0 version.
read_when:
  - cutting a release, or changing the release workflow
  - bumping the version in pyproject.toml
  - deciding how a repo using qmstrace installs or upgrades it
---

# Releasing qmstrace

A release is a tag `vX.Y.Z` on `main` and a GitHub release that carries the CHANGELOG's
section for it and the wheel. A release is installed from
the tag with `uv tool install --python 3.13 "git+https://github.com/Lightbridge-KS/qmstrace@vX.Y.Z"`;
nothing is published to a package index.

- **The version** lives in `pyproject.toml` alone. `qmstrace --version` reads it from the
  installed distribution, and `uv.lock` records it, so a change to it is followed by
  `uv lock` (CI installs with `uv sync --locked`).
- **The tag** is the one human release act: annotated, named `v` and the version. The
  release workflow refuses a tag that does not match `pyproject.toml`.
- **Release tags are not baselines.** `vX.Y.Z` does not match `baseline/requirements/<n>`,
  so a release freezes no requirement. A requirements baseline is cut on its own.

## Steps

1. **Prepare, on a branch with a pull request.**
   - In `CHANGELOG.md`, move the `[Unreleased]` entries under `## [X.Y.Z] - YYYY-MM-DD`,
     leave `## [Unreleased]` empty above it, and add the version's link at the bottom.
   - Set `version = "X.Y.Z"` in `pyproject.toml`, then run `uv lock`.
   - `just dry` passes, and so do both trace gates.
2. **Merge it.** CI on `main` passes on the merge commit.
3. **Tag the merge commit and push the tag:**

    ```sh
    git switch main && git pull --ff-only
    git tag -a vX.Y.Z -m "qmstrace X.Y.Z"
    git push origin vX.Y.Z
    ```

4. **Review the draft.** `.github/workflows/release.yml` runs the dry gate on the tagged
   commit, checks the tag against the version, and drafts the release with the CHANGELOG
   section as its notes and the wheel attached. Read the notes, then publish the draft.
5. **Move `main` on**, in a pull request: `version = "X.Y+1.0.dev0"` and `uv lock`, so a
   build from `main` never claims a released number.

**A patch from `main`.** When everything on `main` since the last release may ship —
`git log vX.Y.Z..main` lists it — a patch is cut from `main` with the same steps: step 1
sets `X.Y.Z+1` over the `.dev0` version, and step 5 sets that `.dev0` version back. When
`main` also holds work that must not ship yet, a patch needs a branch from the tag instead;
that path is not set up.

If the workflow fails, fix the cause on `main`, delete the tag (`git push origin :vX.Y.Z`,
`git tag -d vX.Y.Z`) and any draft it left, and tag again. A published release's tag is
never moved.

**Refreshing an unpublished candidate.** Additional merged work needs a release-refresh PR
that updates the version's existing CHANGELOG section and repeats candidate verification.
After that PR merges and its merge CI passes, explicit rebuild authorization permits removing
the obsolete draft and local/remote tag and pushing a new annotated tag at that exact commit.
Remove the old draft before pushing: the workflow creates a draft rather than replacing one.
Recheck that the release is still unpublished before removing anything. Review the replacement
CI wheel and notes before publication; a refresh PR alone changes neither tag nor draft.
