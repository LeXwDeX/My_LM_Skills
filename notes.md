# Notes: Fix empty folder contents on GitHub

## Findings
- `anthropics-skills` and `planning-with-files` are tracked as gitlinks (mode 160000) in this repo; no `.gitmodules` file exists.
- Both directories currently contain their own `.git` folders, meaning they were added as nested repos/submodules.
- GitHub will display these as submodule pointers instead of the actual files, which matches the issue the user saw.

## Plan implications
- Remove nested `.git` directories and the gitlink entries.
- Re-add the folders as regular tracked files so GitHub shows full contents.
