# Changelog

## [11.5.0-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.4.1-alpha.1...v11.5.0-alpha.1) (2026-02-28)


### Features

* enrich transcoder job card with poster, type badge, and metadata ([c27c48e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c27c48ec5fe2332adfec5419232bfcc86d5c9782))

## [11.4.1-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.4.0-alpha.1...v11.4.1-alpha.1) (2026-02-28)


### Bug Fixes

* increase transcoder client timeout to 15s read / 5s connect ([f91a9a0](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/f91a9a00a8babaf0f8b022d0cb1ce76b969844a9))

## [11.4.0-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.3.0-alpha.1...v11.4.0-alpha.1) (2026-02-28)


### Features

* per-job transcoder log previews and plain-text log parsing ([0b843bd](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/0b843bdba165886f6f29abcb920999ac1326c6a6))


### Bug Fixes

* update plain text log parser test to match regex parsing ([ab6be9b](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/ab6be9b8833fbf15a289144ee711bc985388c09c))

## [11.3.0-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.2.0-alpha.1...v11.3.0-alpha.1) (2026-02-28)


### Features

* progress bar tracks overall disc, per-job pause, year parsing fix, review pane improvements ([e958f6d](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/e958f6dd019822b02fbc7e3a5203d4ba5b87e1c4))
* show log_level_libraries on transcoder config page ([be060e7](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/be060e7d3b76dcfcdfc59368fd39eb2f7526ebf7))
* sortable column headers on log pages ([a447f7e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/a447f7e66338bd1751ea65a1566ae975ee055fd6))
* structured logging with StructuredLogViewer for ARM and transcoder ([cf222f1](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/cf222f191d1e47f00012e44545f1a1debfd34442))
* switch favicon to white ARM logo ([36d950e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/36d950e56ea216948c1f4309ab9917109ace080d))


### Bug Fixes

* catch RuntimeError and OSError in httpx client exception handlers ([c0d56a5](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c0d56a50347cd1a04c6a466df5992df40f195135))
* prevent FOUC by hiding body until CSS loads ([99313a1](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/99313a165054b3ebf69e825d7808a58e613262f6))
* prevent layout jump in review widget InlineLogFeed ([9fb6196](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/9fb61966f973a37a4874557b1f1617b4eea1dc44))
* rename "Accepting Discs" toggle label to "Auto-Start" ([001054d](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/001054dad74162940bdb777fb76760aaee106ca9))
* serve root-level static files and prevent path traversal in SPA catch-all ([c190797](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c190797b4ffcc4280579eb9dc2649652f572a98a))
* TMDb metadata provider fallback, error handling, and logging ([b075b1b](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/b075b1b44db7b5bfb1423523fbeb4635192ba482))

## [11.2.0-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.1.1-alpha.1...v11.2.0-alpha.1) (2026-02-28)


### Features

* add connection status visibility for ARM and transcoder services ([044660c](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/044660c015ad728d1e2f6ea7ccaad89fb3a91898))
* add MusicBrainz search for audio CDs ([938fb6e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/938fb6e8a0cf1a87232442e0d27a8019e1ce5b20))
* add structured fields, track comparison, and card flip animation ([b90fb3e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/b90fb3e8266c9246e71620b518014aeaf5ecdddd))


### Bug Fixes

* harden MusicBrainz search and cover art handling ([c6127f1](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c6127f1ae539bd47b439a666adb65284a1a23170))
* remove redundant type comparison in MusicSearch flip card ([c1b88fb](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c1b88fb365335d9ab9cae5b5d7520a7491eb5fc7))

## [11.1.1-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.1.0-alpha.1...v11.1.1-alpha.1) (2026-02-26)


### Bug Fixes

* send plain media title in webhook payload ([17a5310](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/17a531010245b77563772f4b30ebb87b92f098dd))
* use vivid primary bg for review status bar on dark themes ([f1dab61](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/f1dab61e25f99ea91259048d91fe036c13046741))

## [11.1.0-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.0.1-alpha.1...v11.1.0-alpha.1) (2026-02-26)


### Features

* add CRC database lookup and submit to job detail and review widget ([28ca62d](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/28ca62d7d611f67925a1ce4b50c4504b8afeea4b))


### Bug Fixes

* restore pointer cursor on buttons for Tailwind v4 ([6fb102e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/6fb102e8664d900b4ff3193326965322dda15f38))

## [11.0.1-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.0.0-alpha.1...v11.0.1-alpha.1) (2026-02-26)


### Bug Fixes

* remove dead RIPMETHOD_DVD and RIPMETHOD_BR config fields ([1077a62](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/1077a62aa55e5ec6515de057717a58d20ab7e866))
* replace hardcoded paths with env vars in standalone compose ([5d365bb](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/5d365bbe45ac067dd04ff8dec0345ebd8a1ba68d))

## [11.0.0-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v10.1.0-alpha.1...v11.0.0-alpha.1) (2026-02-25)


### ⚠ BREAKING CHANGES

* /api/settings/bash-script endpoints removed.

### Features

* replace bash script notification with ARM config fields ([be3e548](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/be3e54898ff3b451b5720d24381385607af16664))

## [10.1.0-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v10.0.0-alpha.1...v10.1.0-alpha.1) (2026-02-25)


### Features

* add 14 color scheme themes with LCARS styling and sidebar layout refinements ([bf05167](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/bf051673ba6866e61c1948b85ebfba17367f5b9f))
* add disc type icon to review widget and minor cleanup ([48ac784](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/48ac784b7952072e7893927570a7613799157594))
* Add settings page, transcoder management, and log viewer ([7f82eb4](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/7f82eb4cffe76cadb3c30a955016759b37cf9e6c))
* add test coverage reporting with Codecov ([58891f4](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/58891f4a6465700427bb3bb9b33189b932901dbe))
* Add title search and metadata matching to job detail page ([85e4487](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/85e4487193634655dff3ed204abbe0e3f8f64437))
* add UHD capable toggle for Blu-ray drives ([5d1363d](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/5d1363d64630214b969acaa8aafcee7b414e4dfd))
* **api:** add frontend API layer and types for new backend features ([ec201a5](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/ec201a5d7f82ddbd94a6cc6e57d4b643384102e5))
* **backend:** add system monitoring, job control, and metadata testing ([ed51a3b](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/ed51a3b922486d44288db7e77c0b36cbc8622982))
* **components:** add system stats, disc review, and rip settings components ([d83efca](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d83efca113991207ed45b3773a469663baf31ff0))
* dashboard improvements — drive names, disc icons, editable metadata, 4K UHD support, favicon, page titles ([ed497d3](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/ed497d3a295330e7417ccd589bf1e5cdf453ea79))
* display transcoder live stats (CPU, temp, memory) in sidebar ([2b6ff34](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/2b6ff3491c216fe8b48cfa486611ac2bf1a070b8))
* expose imdb_id and poster_url auto/manual variants in API schema ([26a51fe](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/26a51fe73dfa172755dc7086ad920abf6612ee6c))
* LCARS theme panel redesign with structural frames and pill inputs ([c048b08](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c048b080d683750d96468cd30bdef7f42013993b))
* notify ARM-neu to update submodule on release ([b1bdd35](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/b1bdd3572d555adf23b506457491fc7db0327885))
* **settings:** overhaul settings with search, metadata testing, and appearance ([076f2d0](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/076f2d02229d5a45094370df25203c26ba333511))
* **theme:** add customizable color scheme system ([81371b2](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/81371b2253bafbfded7af846a779a6ba62b9e81d))
* track progress on dashboard cards + auto-refresh job detail ([acca233](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/acca233fa896b3c373b89ec41563a601e90d66d3))
* **ui:** integrate theme system and enhance dashboard, drives, and jobs ([d10e45c](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d10e45c1446e07d5c756b9387e3a80d21aa5107f))


### Bug Fixes

* add missing drive_names to emptyDashboard in store ([9d7ef4d](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/9d7ef4de970fee9e5db65d011bd175294e8d7e0d))
* add missing transcoder_system_stats to +page.svelte default ([d431bdf](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d431bdffea151c288bd6309c3bca0a783681ebb2))
* add null guard for settings in armSettingsSection snippet ([fc334f9](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/fc334f9d545043ba836dadee6b31556dc850e252))
* add spacing between CPU percent and temperature display ([549e173](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/549e173e31dc54b387a22481a28c65b53a083621))
* configure release-please to update VERSION file ([d453a07](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d453a07a50950e3057953b1ab83cb293f6c92209))
* display friendly disc type labels instead of raw values ([ea7bf8b](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/ea7bf8b79e399013c988684e2095a15de46c3f0b))
* pin frontend build stage to native platform for multi-arch builds ([407e856](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/407e8562990772c085c62ca4567d57fe0e32082f))
* remove UNIDENTIFIED_EJECT from settings page ([4ad9835](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/4ad98352117d68356422e8a18a47db32c5625fd0))
* resolve 6 TypeScript errors in frontend type checking ([e4d9ceb](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/e4d9ceb9226e6b1a50fbe903c2c66b3ec475b5b5))
* resolve all svelte-check warnings ([4526227](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/4526227d3d0180032e6c59ddcdbd778795454e08))
* Resolve dashboard transcoder section flickering ([7d3add6](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/7d3add64c9617e9f05adab3a4584b2c832d2ddd3))
* resolve flake8 lint errors ([a141cee](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/a141cee18e0ee44d452a90f6707a939bdae71ca7))
* show storage section on transcoder tab ([17cb5b5](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/17cb5b54f5e422a5841daa8a6bec12dabff27a55))
* sync Config model with actual ARM database schema ([5306dab](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/5306dabbb5f10f006e8e471ff1330afe25bcbc4e))
* sync Config model with ARM DB schema and add missing active statuses ([fe950c1](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/fe950c191df8086deac9ca4fd7af6d6a4f6f6668))
* use DOCKERHUB_USERNAME secret for image name ([7d14038](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/7d140384de6b65a7dae86b270df04bddd8e5e502))
* use non-breaking space for CPU temp separator ([48c8cc4](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/48c8cc45f9c91e5518f3843bdc357393c502ec51))
* use PAT for release-please so releases trigger publish workflow ([53e4128](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/53e41281d6a917493255b1814c5fcaebcadbba07))
* use RELEASE_PAT for parent repo dispatch ([713c21a](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/713c21af09d0e84c8dd79a950bcbed7aca4fbb06))

## [0.9.0](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v0.8.0...v0.9.0) (2026-02-22)


### Features

* add 14 color scheme themes with LCARS styling and sidebar layout refinements ([bf05167](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/bf051673ba6866e61c1948b85ebfba17367f5b9f))
* LCARS theme panel redesign with structural frames and pill inputs ([c048b08](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c048b080d683750d96468cd30bdef7f42013993b))

## [0.8.0](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v0.7.0...v0.8.0) (2026-02-20)


### Features

* expose imdb_id and poster_url auto/manual variants in API schema ([26a51fe](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/26a51fe73dfa172755dc7086ad920abf6612ee6c))

## [0.7.0](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v0.6.0...v0.7.0) (2026-02-20)


### Features

* track progress on dashboard cards + auto-refresh job detail ([acca233](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/acca233fa896b3c373b89ec41563a601e90d66d3))


### Bug Fixes

* sync Config model with actual ARM database schema ([5306dab](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/5306dabbb5f10f006e8e471ff1330afe25bcbc4e))
* sync Config model with ARM DB schema and add missing active statuses ([fe950c1](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/fe950c191df8086deac9ca4fd7af6d6a4f6f6668))

## [0.6.0](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v0.5.0...v0.6.0) (2026-02-19)


### Features

* add disc type icon to review widget and minor cleanup ([48ac784](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/48ac784b7952072e7893927570a7613799157594))
* add test coverage reporting with Codecov ([58891f4](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/58891f4a6465700427bb3bb9b33189b932901dbe))
* add UHD capable toggle for Blu-ray drives ([5d1363d](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/5d1363d64630214b969acaa8aafcee7b414e4dfd))


### Bug Fixes

* display friendly disc type labels instead of raw values ([ea7bf8b](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/ea7bf8b79e399013c988684e2095a15de46c3f0b))

## [0.5.0](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v0.4.2...v0.5.0) (2026-02-19)


### Features

* dashboard improvements — drive names, disc icons, editable metadata, 4K UHD support, favicon, page titles ([ed497d3](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/ed497d3a295330e7417ccd589bf1e5cdf453ea79))


### Bug Fixes

* add missing drive_names to emptyDashboard in store ([9d7ef4d](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/9d7ef4de970fee9e5db65d011bd175294e8d7e0d))
* resolve all svelte-check warnings ([4526227](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/4526227d3d0180032e6c59ddcdbd778795454e08))

## [0.4.2](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v0.4.1...v0.4.2) (2026-02-18)


### Bug Fixes

* remove UNIDENTIFIED_EJECT from settings page ([4ad9835](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/4ad98352117d68356422e8a18a47db32c5625fd0))

## [0.4.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v0.4.0...v0.4.1) (2026-02-16)


### Bug Fixes

* configure release-please to update VERSION file ([d453a07](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d453a07a50950e3057953b1ab83cb293f6c92209))

## [0.4.0](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v0.3.0...v0.4.0) (2026-02-16)


### Features

* notify ARM-neu to update submodule on release ([b1bdd35](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/b1bdd3572d555adf23b506457491fc7db0327885))


### Bug Fixes

* use PAT for release-please so releases trigger publish workflow ([53e4128](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/53e41281d6a917493255b1814c5fcaebcadbba07))
* use RELEASE_PAT for parent repo dispatch ([713c21a](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/713c21af09d0e84c8dd79a950bcbed7aca4fbb06))

## [0.3.0](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v0.2.0...v0.3.0) (2026-02-16)


### Features

* display transcoder live stats (CPU, temp, memory) in sidebar ([2b6ff34](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/2b6ff3491c216fe8b48cfa486611ac2bf1a070b8))


### Bug Fixes

* add missing transcoder_system_stats to +page.svelte default ([d431bdf](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d431bdffea151c288bd6309c3bca0a783681ebb2))
* add spacing between CPU percent and temperature display ([549e173](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/549e173e31dc54b387a22481a28c65b53a083621))
* pin frontend build stage to native platform for multi-arch builds ([407e856](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/407e8562990772c085c62ca4567d57fe0e32082f))
* resolve 6 TypeScript errors in frontend type checking ([e4d9ceb](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/e4d9ceb9226e6b1a50fbe903c2c66b3ec475b5b5))
* resolve flake8 lint errors ([a141cee](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/a141cee18e0ee44d452a90f6707a939bdae71ca7))
* show storage section on transcoder tab ([17cb5b5](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/17cb5b54f5e422a5841daa8a6bec12dabff27a55))
* use DOCKERHUB_USERNAME secret for image name ([7d14038](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/7d140384de6b65a7dae86b270df04bddd8e5e502))
* use non-breaking space for CPU temp separator ([48c8cc4](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/48c8cc45f9c91e5518f3843bdc357393c502ec51))

## [0.2.0](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v0.1.0...v0.2.0) (2026-02-15)


### Features

* Add settings page, transcoder management, and log viewer ([7f82eb4](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/7f82eb4cffe76cadb3c30a955016759b37cf9e6c))
* Add title search and metadata matching to job detail page ([85e4487](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/85e4487193634655dff3ed204abbe0e3f8f64437))
* **api:** add frontend API layer and types for new backend features ([ec201a5](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/ec201a5d7f82ddbd94a6cc6e57d4b643384102e5))
* **backend:** add system monitoring, job control, and metadata testing ([ed51a3b](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/ed51a3b922486d44288db7e77c0b36cbc8622982))
* **components:** add system stats, disc review, and rip settings components ([d83efca](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d83efca113991207ed45b3773a469663baf31ff0))
* **settings:** overhaul settings with search, metadata testing, and appearance ([076f2d0](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/076f2d02229d5a45094370df25203c26ba333511))
* **theme:** add customizable color scheme system ([81371b2](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/81371b2253bafbfded7af846a779a6ba62b9e81d))
* **ui:** integrate theme system and enhance dashboard, drives, and jobs ([d10e45c](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d10e45c1446e07d5c756b9387e3a80d21aa5107f))


### Bug Fixes

* Resolve dashboard transcoder section flickering ([7d3add6](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/7d3add64c9617e9f05adab3a4584b2c832d2ddd3))

## Changelog
