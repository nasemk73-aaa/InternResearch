# AGENTS.md

## Hotfix Release Playbook

Current release behavior in this repo:
- Pushing a tag matching `vX.Y.Z` triggers `.github/workflows/release.yml`.
- That workflow creates/updates the GitHub Release and uploads platform binaries.
- It does **not** publish crates to crates.io.

### Steps (security hotfix)
1. Prepare release commit on `master`:
   - Update `Cargo.toml` version (for example `0.11.1`).
   - Update `CHANGELOG.md` from `Unreleased` to the new version/date.
2. Validate locally:
   - `cargo test`
   - `cargo test --manifest-path utf16-simd/Cargo.toml`
   - `cargo publish --dry-run`
3. Publish crates to crates.io (manual, if needed):
   - Publish `utf16-simd` first **only** if its version changed.
     - `cargo publish --manifest-path utf16-simd/Cargo.toml`
   - Then publish `evtx`:
     - `cargo publish`
4. Create and push the tag:
   - `git tag vX.Y.Z`
   - `git push origin vX.Y.Z`
5. Verify release:
   - Confirm crates.io shows the new versions.
   - Confirm CI succeeded via GitHub CLI:
     - `gh run list --workflow release.yml --limit 5`
     - `gh run watch <run-id>`
   - Confirm release artifacts exist:
     - `gh release view vX.Y.Z`
