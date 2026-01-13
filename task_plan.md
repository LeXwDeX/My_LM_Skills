# Task Plan: Fix empty folder contents on GitHub

## Goal
Ensure the `anthropics-skills` and `planning-with-files` folders show their actual contents on GitHub by removing submodule artifacts and committing the files directly.

## Phases
- [x] Phase 1: Plan and setup
- [x] Phase 2: Research/gather information
- [x] Phase 3: Execute/build
- [x] Phase 4: Review and deliver

## Key Questions
1. Are these folders currently tracked as git submodules or gitlinks?
2. Should the fix vendor the contents or restore proper submodule config with `.gitmodules`?
3. What cleanup is needed to remove nested git metadata safely?

## Decisions Made
- Decide to vendor the contents of both folders as normal tracked files (remove submodule gitlinks) so GitHub displays contents directly.

## Errors Encountered
- None yet

## Status
**Complete** - Submodule artifacts removed; directories tracked as regular files; ready to push
