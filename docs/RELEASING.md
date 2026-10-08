# Releasing

EmojiToText releases use datestamp versions in `YYYY-MM-DD` form, and a human cuts every release.

## Release Process

1. Confirm the pinned upstream tag in `tools/generate_map.py` is the intended one.
2. Add the `CHANGELOG.md` entry for the release date in a normal commit on the default branch.
3. Run the Release workflow (`workflow_dispatch`) with the `date` input and the optional `dry_run` flag.
4. Verify the datestamp tag, the GitHub Release notes, and the source archives.

## Workflow Behavior

- The workflow refreshes to the latest upstream `iamcal/emoji-data` tag.
- It fails if upstream is unreachable or the `CHANGELOG.md` entry for the date is missing.
- The `dry_run` input runs the refresh and tests, prints the diff, and skips the push, tag, and Release.
- A same-day re-release moves the datestamp tag to the new commit and updates the existing Release in place.
- Each Release carries the matching `CHANGELOG.md` section as its notes plus the automatic source archives.

## Manual Fallback

Use this only when the release runner is broken.

1. Run `make release DATE=YYYY-MM-DD`.
2. Push the release commit to the default branch.
3. Force-move the tag with `git tag -f YYYY-MM-DD` and `git push -f origin YYYY-MM-DD`.
4. Create or edit the GitHub Release for the tag, using the changelog section as the notes.

## Recovery

A refresh writes several files, so an interrupted run can leave a partial tree.
Discard the partial changes with `git checkout -- <paths>`, then re-run the release.
