# PlayerTrack Enhanced

Version 3.8.0.0. Add this custom repository in Dalamud Settings > Experimental > Custom Plugin Repositories:

https://raw.githubusercontent.com/cloudesh/ptenhanced/main/repo.json

Then open /xlplugins and install PlayerTrack Enhanced. Future updates use this same URL.

This build allows the currently logged-in character only when its exact name is M'aya Noh, Naomi Yoshizawa or Leon Glaves. Names are checked on any home world; this is a local access check, not server authentication or tamper protection. Other characters and alts are restricted. The startup notifier reports the approved startup character name to the maintainer through Discord. The endpoint is reversibly encoded and is not secret storage.

PTOM sound is optional and enabled by default. Update notes appear until dismissed, with the previous five releases available in the same window.

## Upload this release

Extract the GitHub-ready ZIP, then upload this folder's CONTENTS to the root of the main branch of https://github.com/cloudesh/ptenhanced. The root must contain repo.json and the plugins folder. Do not upload the outer GitHub-ready ZIP as a single repository file. The nested latest.zip is the compiled plugin and must stay zipped. No GitHub Pages configuration or extra GitHub release is needed for this layout.

For future updates, upload the new version's plugins folder and replace repo.json from its GitHub-ready package. Keep the older version folders if desired. Friends keep their existing repository URL. Check the raw JSON and ZIP links in a signed-out browser before sharing them.

GitHub Actions validates the index, ZIP, checksum and licences on pushes and pull requests. The maintainer's local Publish-GitHubRelease.ps1 pipeline builds and runs all checks before pushing. It requires no repository secrets in GitHub Actions. The pipeline files under .github must be included when uploading this package manually.

This distribution repository is public. Anyone can download or inspect its files, and the local access check can be modified. See RELEASE_NOTES.md and the included licences. Source code is supplied separately to the maintainer.