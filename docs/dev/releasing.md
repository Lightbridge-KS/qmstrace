---
summary: How a qmstrace release is cut — the version lives in pyproject.toml, an annotated vX.Y.Z tag is the one human act, the release workflow gates the tag and drafts a GitHub release from the CHANGELOG with the wheel, a maintainer publishes it, and main moves on to the next .dev0 version.
read_when:
  - cutting a release, or changing the release workflow
  - bumping the version in pyproject.toml
  - deciding how a repo using qmstrace installs or upgrades it
---

# Releasing qmstrace

A release is a tag `vX.Y.Z` on `main` and a GitHub release that carries the CHANGELOG's
section for it and the wheel. The repository is private, so a release is installed from
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

If the workflow fails, fix the cause on `main`, delete the tag (`git push origin :vX.Y.Z`,
`git tag -d vX.Y.Z`) and any draft it left, and tag again. A published release's tag is
never moved.
