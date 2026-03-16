# Changelog

## [13.1.0](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v13.0.1...v13.1.0) (2026-03-16)


### Features

* add copying/ejecting statuses, fix transcoder status label ([e25b6fe](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/e25b6fe0230f65666a74e1cafe909190a184c9f7))
* add theme name field to upload form ([9b4f00a](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/9b4f00a2aa186f812d8224e0a4bd17863bb787c8))
* extractable theme system with runtime CSS injection ([4ec7906](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/4ec7906d41dcc80814876e62d42cde8b01696407))
* improve metadata error messaging and test-with-unsaved-key ([14e9325](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/14e9325dfbef22780d05de2b08fe46c092aedd14))
* load theme CSS from sidecar files, save as split files ([02db072](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/02db0720904fc7b7a3ce5b877fa4558485d7adcc))
* multipart theme upload and CSS download in API client ([3ec182a](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/3ec182a0d41570e2ff7b167e684e2c8d79d0eedb))
* multipart theme upload, separate CSS download endpoint ([912c95f](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/912c95f48d9d36a96195e9c5dacacb04f873e06b))
* two-field theme upload UI (JSON + CSS) ([aed7025](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/aed702507686904cd961c7f760393b8e615633bd))


### Bug Fixes

* address SonarCloud issues in theme code ([bf36830](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/bf36830cd3eb52f32283378a2e092e60dcc397b1))
* export downloads both JSON and CSS as separate files ([015db27](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/015db27bbb832273984c5bb9a7717e1ee4f289fe))
* inline resolve() path containment checks for SonarCloud taint analysis ([4d95033](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/4d95033cb0ef6e39936090df81dbe79e462819b6))
* update tests for metadata error passthrough and params changes ([2a4feb9](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/2a4feb9bac61e38b40e9f9aa07588284f4f3c057))
* use resolve()-based path containment check for theme file writes ([6b4a575](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/6b4a575e1c4f838f2f17d5d4694ee95f3cea7995))
* use yellow status color for copying/ejecting statuses ([a801aa5](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/a801aa50004eeed9f1c12d09b55e027448e14744))

## [13.0.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v13.0.0...v13.0.1) (2026-03-15)


### Bug Fixes

* add info tooltip to UHD Capable checkbox ([172491f](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/172491fffc468dfa32e96f6ead579cdeb3da5347))

## [13.0.0](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v12.0.0...v13.0.0) (2026-03-14)


### ⚠ BREAKING CHANGES

* version alignment for v12 release

### Features

* abcde.conf editor, music file browser, webhook test fallback ([383d03e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/383d03ebbf08b47fd3bb9f228005634bfc2efe27))
* add AUDIO_FORMAT to rip settings UI ([abcfcfd](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/abcfcfd4caaeb0b5b8dca4a914586f66113a95da))
* add Force Scan button and udev diagnostic panel on Drives tab ([0130fa3](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/0130fa34db67acf5ba1ef81334f39f6897bb0db5))
* add Force Scan button on drive cards ([d1ecc13](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d1ecc136acba6e9adeebcce4c91918fa37e3a9fa))
* add per-job transcoder log view on job detail page ([f9eb981](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/f9eb98104d587ea46686328fcac49d98b54740bf))
* add track update API, multi-title backend proxy, and supporting changes ([cea5a74](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/cea5a74081f0612b9fa8feb45bb6fa2791894a1e))
* layout nav, dashboard idle state, LCARS section headers ([d2089e9](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d2089e9a10f3b48f00bb83f1265c3a438ac2e80b))
* multi-title disc support — UI + backend proxy ([8ee4bae](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/8ee4baec8f02e43c80c3dcdf64ff4d5d84ab3190))
* music track display, disc info, collapsible debug, transcoder config ([d02fb70](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d02fb703ab588f72f33c108f1af4ea717bde943c))
* notifications page with dismiss support ([0ed3e77](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/0ed3e778f2466e1df7ad4f32549fd30c3dec7aea))
* polish TVDB match panel and job detail UX ([d67a6fa](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d67a6fad6513ce560ac8f1904f17177d99a1eec2))
* replace track enabled buttons with checkboxes and remove Edit column ([77cd4c6](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/77cd4c67856853f6f6b5cb99f4d597c86bef56c7))
* settings deep linking, TVDB config, endpoint popovers, UX polish ([5332a84](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/5332a84a7e4ad421e1ef99a21d8a0321b2bf85c6))
* show DB migration status and fix Hollywood theme borders ([07a47a4](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/07a47a423040ffcb0b7de02cc5c9a0036e9d6255))
* show disc number on dashboard cards and table view ([fb2800e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/fb2800e72a504f910d6fd13d1916deda72277c6a))
* stale drive removal and diagnostic panel improvements ([b7e9623](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/b7e96237665b76ef2618a7d60477f60b8c8ed0f1))
* structured diagnostic panel with table layout ([216398f](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/216398f9d1524b50226ba05ab825b0cf407ff7b8))
* TVDB multi-season matching panel and episode columns ([de0ddaa](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/de0ddaae62047b1d05f25e3cd9327169185898d3))
* UI polish — status labels, waiting_transcode, component fixes ([c257cd5](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c257cd55531843f15ae29628b8d6d14e809acfd5))


### Bug Fixes

* add abcde music progress parsing to UI progress endpoint ([828f6fc](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/828f6fc4b792b9dc9824cc4db4e1d39fc018fdce))
* add border and padding to lcars-body for non-LCARS themes ([4426b4f](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/4426b4f72a9365f68c8d4436ca58fab896513269))
* add season/episode/artist/album columns to Job model ([119862a](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/119862a60d2fa81c6efcf35a0479c786ee7c41b1))
* exclude stale drives from drives_online count and fix track mock ([0fbcf0e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/0fbcf0eccaa91a8f3d45b0aa9fecd9fd776b7728))
* Hollywood theme panel borders, hr styling, and tab headings ([9eabe3b](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/9eabe3b2c456ca6716fa27f3f53f9d273075f056))
* make confirm dialog opaque in themes with semi-transparent surfaces ([64e0cad](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/64e0cad05af282e498f2ca8320b071895c83fd3a))
* resolve SonarCloud issues and frontend type errors ([3f69246](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/3f6924683d254c73fd77ad2da6f7874c388ee670))
* resolve test failures and add coverage for abcde config endpoints ([27b75c3](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/27b75c3e8f92589a9cab629a1bcd90d3db51a85f))
* restore VERSION to 12.0.0 (already released) ([478520e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/478520e96b5d492edec380397a0efb59aab37728))
* support ARM_LOGS_PATH override for production log mount ([3f4aa52](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/3f4aa52e3534a7bdb6a16e90b192e62841c953e0))
* track enabled column + countdown timer start time ([a3ef25d](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/a3ef25df473da42712588f021109ab7ae6dbf077))
* TVDB panel delta display and season=0 handling ([6e00596](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/6e00596174046f5370d2bb4d1c5396c6e17df0e5))
* use primary color tokens for files page warning banner ([2ae53ce](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/2ae53ce88a59c2b194da0c0e8f0b5430897e24fb))
* use primary colors for toggle, fix LCARS tab styling, filter stale drives ([b99f8db](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/b99f8db83417c2120a236d919ef848331e04824c))
* zero-track rip guard, error display, progress fallback to no_of_titles ([fea1bdf](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/fea1bdf66b112d273252d2970b5144cbb3be9fc2))


### Miscellaneous Chores

* set pre-release version for 12.0.0 ([abbcd9b](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/abbcd9b34f7db27116295d8c40ca3d91aeaa1c61))

## [12.0.0](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.13.3...v12.0.0) (2026-03-09)


### ⚠ BREAKING CHANGES

* /api/settings/bash-script endpoints removed.

### Features

* add 14 color scheme themes with LCARS styling and sidebar layout refinements ([bf05167](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/bf051673ba6866e61c1948b85ebfba17367f5b9f))
* add connection status visibility for ARM and transcoder services ([044660c](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/044660c015ad728d1e2f6ea7ccaad89fb3a91898))
* add CRC database lookup and submit to job detail and review widget ([28ca62d](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/28ca62d7d611f67925a1ce4b50c4504b8afeea4b))
* add disc type icon to review widget and minor cleanup ([48ac784](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/48ac784b7952072e7893927570a7613799157594))
* add MusicBrainz search for audio CDs ([938fb6e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/938fb6e8a0cf1a87232442e0d27a8019e1ce5b20))
* Add settings page, transcoder management, and log viewer ([7f82eb4](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/7f82eb4cffe76cadb3c30a955016759b37cf9e6c))
* add structured fields, track comparison, and card flip animation ([b90fb3e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/b90fb3e8266c9246e71620b518014aeaf5ecdddd))
* add test coverage reporting with Codecov ([58891f4](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/58891f4a6465700427bb3bb9b33189b932901dbe))
* Add title search and metadata matching to job detail page ([85e4487](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/85e4487193634655dff3ed204abbe0e3f8f64437))
* add UHD capable toggle for Blu-ray drives ([5d1363d](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/5d1363d64630214b969acaa8aafcee7b414e4dfd))
* add warning banner to file browser page ([e16451e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/e16451e59c4186a10b2d156f6eff55e08d9cb6e9))
* **api:** add frontend API layer and types for new backend features ([ec201a5](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/ec201a5d7f82ddbd94a6cc6e57d4b643384102e5))
* **backend:** add system monitoring, job control, and metadata testing ([ed51a3b](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/ed51a3b922486d44288db7e77c0b36cbc8622982))
* bulk delete with confirmation, match tab styling to settings ([776bacb](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/776bacbf37e9997db4df9bff89e70fe20ef55084))
* **components:** add system stats, disc review, and rip settings components ([d83efca](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d83efca113991207ed45b3773a469663baf31ff0))
* condense dashboard into unified status bar ([52d8e08](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/52d8e08c160559ff4878fa6f840044f43aa205d6))
* dashboard improvements — drive names, disc icons, editable metadata, 4K UHD support, favicon, page titles ([ed497d3](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/ed497d3a295330e7417ccd589bf1e5cdf453ea79))
* display folder sizes in file browser ([6c650ea](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/6c650eaf11772959d85ba1da3b5b7f00009f7d24))
* display transcoder live stats (CPU, temp, memory) in sidebar ([2b6ff34](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/2b6ff3491c216fe8b48cfa486611ac2bf1a070b8))
* enrich transcoder job card with poster, type badge, and metadata ([c27c48e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c27c48ec5fe2332adfec5419232bfcc86d5c9782))
* expose imdb_id and poster_url auto/manual variants in API schema ([26a51fe](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/26a51fe73dfa172755dc7086ad920abf6612ee6c))
* file browser with browsable move dialog ([af13ab2](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/af13ab2719b7983d4ebe4904769ff7b1d83c9aba))
* file permissions display, fix-permissions, host paths, bulk delete fix ([a2be5d4](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/a2be5d4a9f2e0ede9337d29979a9e0d24e68f168))
* LCARS theme panel redesign with structural frames and pill inputs ([c048b08](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c048b080d683750d96468cd30bdef7f42013993b))
* move drives page into settings as a tab ([f494bd7](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/f494bd7a7897993979e493aab1c76004e60226bb))
* move stats bar and auto-start toggle to global header, add themes ([480cebc](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/480cebcf041fc03699a278bd5342c1653becd8d2))
* notify ARM-neu to update submodule on release ([b1bdd35](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/b1bdd3572d555adf23b506457491fc7db0327885))
* per-job transcode config overrides UI ([f0638b3](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/f0638b32ce42d3e14aaa5725de2d7b7fad2b19f9))
* per-job transcoder log previews and plain-text log parsing ([0b843bd](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/0b843bdba165886f6f29abcb920999ac1326c6a6))
* progress bar tracks overall disc, per-job pause, year parsing fix, review pane improvements ([e958f6d](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/e958f6dd019822b02fbc7e3a5203d4ba5b87e1c4))
* proxy metadata requests through ARM API ([6d343f7](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/6d343f7c90522efd79fd392fb579703b06a6fcf5))
* replace bash script notification with ARM config fields ([be3e548](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/be3e54898ff3b451b5720d24381385607af16664))
* **settings:** overhaul settings with search, metadata testing, and appearance ([076f2d0](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/076f2d02229d5a45094370df25203c26ba333511))
* show log_level_libraries on transcoder config page ([be060e7](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/be060e7d3b76dcfcdfc59368fd39eb2f7526ebf7))
* sortable column headers on log pages ([a447f7e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/a447f7e66338bd1751ea65a1566ae975ee055fd6))
* structured logging with StructuredLogViewer for ARM and transcoder ([cf222f1](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/cf222f191d1e47f00012e44545f1a1debfd34442))
* switch favicon to white ARM logo ([36d950e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/36d950e56ea216948c1f4309ab9917109ace080d))
* theme-locked light/dark mode, default card view, error log links ([913e618](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/913e618d8483b2afc9b519778bd6ae5860478cda))
* **theme:** add customizable color scheme system ([81371b2](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/81371b2253bafbfded7af846a779a6ba62b9e81d))
* track progress on dashboard cards + auto-refresh job detail ([acca233](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/acca233fa896b3c373b89ec41563a601e90d66d3))
* **ui:** integrate theme system and enhance dashboard, drives, and jobs ([d10e45c](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d10e45c1446e07d5c756b9387e3a80d21aa5107f))


### Bug Fixes

* add missing drive_names to emptyDashboard in store ([9d7ef4d](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/9d7ef4de970fee9e5db65d011bd175294e8d7e0d))
* add missing transcoder_system_stats to +page.svelte default ([d431bdf](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d431bdffea151c288bd6309c3bca0a783681ebb2))
* add null guard for settings in armSettingsSection snippet ([fc334f9](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/fc334f9d545043ba836dadee6b31556dc850e252))
* add spacing between CPU percent and temperature display ([549e173](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/549e173e31dc54b387a22481a28c65b53a083621))
* address SonarCloud reliability bugs ([d8d5ed7](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d8d5ed7ba54a269fe22a6d4c8c551de2cefc56ad))
* address SonarCloud security findings ([127573e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/127573ed5b084369b019bcb24a75f1b428c2e755))
* breadcrumb hover too dark on dark mode ([3449f94](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/3449f94310d39254b3bf40146a888b29665217e4))
* catch RuntimeError and OSError in httpx client exception handlers ([c0d56a5](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c0d56a50347cd1a04c6a466df5992df40f195135))
* clamp rip progress to 100% when all tracks are ripped ([92f32d1](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/92f32d1c3f4dfc553abac13efa1769698ad5fbcb))
* configure release-please to update VERSION file ([d453a07](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d453a07a50950e3057953b1ab83cb293f6c92209))
* deduplicate job defaults in test factories ([28b80c8](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/28b80c8758ccd28c2cc31c3799cfca5a6c878a92))
* display friendly disc type labels instead of raw values ([ea7bf8b](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/ea7bf8b79e399013c988684e2095a15de46c3f0b))
* exclude colorScheme.ts from SonarCloud duplication detection ([2936e5d](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/2936e5d7e83fd2954c7347afeb08e9196d2e0843))
* harden MusicBrainz search and cover art handling ([c6127f1](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c6127f1ae539bd47b439a666adb65284a1a23170))
* improve font rendering and Blockbuster theme legibility ([2b82738](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/2b82738897675d52c3025a1639c8806172695610))
* increase transcoder client timeout to 15s read / 5s connect ([f91a9a0](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/f91a9a00a8babaf0f8b022d0cb1ce76b969844a9))
* metadata not syncing on review and pause toggle not flipping ([40f4ca0](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/40f4ca0550497d3b1e703e3f6807f78d42df6ea6))
* pin frontend build stage to native platform for multi-arch builds ([407e856](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/407e8562990772c085c62ca4567d57fe0e32082f))
* prevent false 100% progress during MakeMKV scan phase ([11a52d5](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/11a52d5e6fcdb7473cf2514505e8440a9b564fee))
* prevent FOUC by hiding body until CSS loads ([99313a1](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/99313a165054b3ebf69e825d7808a58e613262f6))
* prevent layout jump in review widget InlineLogFeed ([9fb6196](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/9fb61966f973a37a4874557b1f1617b4eea1dc44))
* read full progress file so PRGT phase messages are not missed ([c8c6e62](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c8c6e62279dbdee357db15602f5fede439026782))
* remove dead RIPMETHOD_DVD and RIPMETHOD_BR config fields ([1077a62](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/1077a62aa55e5ec6515de057717a58d20ab7e866))
* remove redundant type comparison in MusicSearch flip card ([c1b88fb](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c1b88fb365335d9ab9cae5b5d7520a7491eb5fc7))
* remove UNIDENTIFIED_EJECT from settings page ([4ad9835](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/4ad98352117d68356422e8a18a47db32c5625fd0))
* rename "Accepting Discs" toggle label to "Auto-Start" ([001054d](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/001054dad74162940bdb777fb76760aaee106ca9))
* replace hardcoded paths with env vars in standalone compose ([5d365bb](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/5d365bbe45ac067dd04ff8dec0345ebd8a1ba68d))
* resolve 44 SonarCloud high-impact code smells ([b0ff5ad](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/b0ff5addbb70a420b4613d1e165279eab4011c1a))
* resolve 6 TypeScript errors in frontend type checking ([e4d9ceb](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/e4d9ceb9226e6b1a50fbe903c2c66b3ec475b5b5))
* resolve all svelte-check warnings ([4526227](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/4526227d3d0180032e6c59ddcdbd778795454e08))
* Resolve dashboard transcoder section flickering ([7d3add6](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/7d3add64c9617e9f05adab3a4584b2c832d2ddd3))
* resolve flake8 lint errors ([a141cee](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/a141cee18e0ee44d452a90f6707a939bdae71ca7))
* resolve remaining 8 SonarCloud high-impact issues ([4c945ea](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/4c945ea8ff8c45a732136235e0dd8b356aea50aa))
* resolve type error in colorScheme test forceDark assertion ([83e52da](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/83e52da08a8fe741b576863a630256933cd9667d))
* resolve TypeScript error and update arm_client tests ([92af79a](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/92af79a0e0a9db19cf37c4b7df36a8fbc5da1c5d))
* restore pointer cursor on buttons for Tailwind v4 ([6fb102e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/6fb102e8664d900b4ff3193326965322dda15f38))
* send plain media title in webhook payload ([17a5310](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/17a531010245b77563772f4b30ebb87b92f098dd))
* serve root-level static files and prevent path traversal in SPA catch-all ([c190797](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c190797b4ffcc4280579eb9dc2649652f572a98a))
* show storage section on transcoder tab ([17cb5b5](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/17cb5b54f5e422a5841daa8a6bec12dabff27a55))
* show waiting_transcode status with yellow color instead of gray ([22dd128](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/22dd1284c03b7928c41f7c975860477d4beed796))
* surface real ARM API errors instead of generic "unreachable" message ([42c8988](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/42c8988c238e347a69fcd24dacca9316ec67d6e2))
* sync Config model with actual ARM database schema ([5306dab](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/5306dabbb5f10f006e8e471ff1330afe25bcbc4e))
* sync Config model with ARM DB schema and add missing active statuses ([fe950c1](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/fe950c191df8086deac9ca4fd7af6d6a4f6f6668))
* TMDb metadata provider fallback, error handling, and logging ([b075b1b](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/b075b1b44db7b5bfb1423523fbeb4635192ba482))
* update plain text log parser test to match regex parsing ([ab6be9b](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/ab6be9b8833fbf15a289144ee711bc985388c09c))
* use DOCKERHUB_USERNAME secret for image name ([7d14038](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/7d140384de6b65a7dae86b270df04bddd8e5e502))
* use non-breaking space for CPU temp separator ([48c8cc4](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/48c8cc45f9c91e5518f3843bdc357393c502ec51))
* use PAT for release-please so releases trigger publish workflow ([53e4128](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/53e41281d6a917493255b1814c5fcaebcadbba07))
* use RELEASE_PAT for parent repo dispatch ([713c21a](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/713c21af09d0e84c8dd79a950bcbed7aca4fbb06))
* use vivid primary bg for review status bar on dark themes ([f1dab61](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/f1dab61e25f99ea91259048d91fe036c13046741))

## [11.13.3-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.13.2-alpha.1...v11.13.3-alpha.1) (2026-03-03)


### Bug Fixes

* metadata not syncing on review and pause toggle not flipping ([40f4ca0](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/40f4ca0550497d3b1e703e3f6807f78d42df6ea6))

## [11.13.2-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.13.1-alpha.1...v11.13.2-alpha.1) (2026-03-03)


### Bug Fixes

* improve font rendering and Blockbuster theme legibility ([2b82738](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/2b82738897675d52c3025a1639c8806172695610))

## [11.13.1-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.13.0-alpha.1...v11.13.1-alpha.1) (2026-03-03)


### Bug Fixes

* deduplicate job defaults in test factories ([28b80c8](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/28b80c8758ccd28c2cc31c3799cfca5a6c878a92))
* exclude colorScheme.ts from SonarCloud duplication detection ([2936e5d](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/2936e5d7e83fd2954c7347afeb08e9196d2e0843))
* resolve 44 SonarCloud high-impact code smells ([b0ff5ad](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/b0ff5addbb70a420b4613d1e165279eab4011c1a))
* resolve remaining 8 SonarCloud high-impact issues ([4c945ea](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/4c945ea8ff8c45a732136235e0dd8b356aea50aa))

## [11.13.0-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.12.2-alpha.1...v11.13.0-alpha.1) (2026-03-03)


### Features

* move stats bar and auto-start toggle to global header, add themes ([480cebc](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/480cebcf041fc03699a278bd5342c1653becd8d2))

## [11.12.2-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.12.1-alpha.1...v11.12.2-alpha.1) (2026-03-02)


### Bug Fixes

* address SonarCloud reliability bugs ([d8d5ed7](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/d8d5ed7ba54a269fe22a6d4c8c551de2cefc56ad))

## [11.12.1-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.12.0-alpha.1...v11.12.1-alpha.1) (2026-03-02)


### Bug Fixes

* address SonarCloud security findings ([127573e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/127573ed5b084369b019bcb24a75f1b428c2e755))

## [11.12.0-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.11.1-alpha.1...v11.12.0-alpha.1) (2026-03-02)


### Features

* display folder sizes in file browser ([6c650ea](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/6c650eaf11772959d85ba1da3b5b7f00009f7d24))

## [11.11.1-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.11.0-alpha.1...v11.11.1-alpha.1) (2026-03-02)


### Bug Fixes

* breadcrumb hover too dark on dark mode ([3449f94](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/3449f94310d39254b3bf40146a888b29665217e4))

## [11.11.0-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.10.0-alpha.1...v11.11.0-alpha.1) (2026-03-02)


### Features

* file permissions display, fix-permissions, host paths, bulk delete fix ([a2be5d4](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/a2be5d4a9f2e0ede9337d29979a9e0d24e68f168))

## [11.10.0-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.9.0-alpha.1...v11.10.0-alpha.1) (2026-03-02)


### Features

* add warning banner to file browser page ([e16451e](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/e16451e59c4186a10b2d156f6eff55e08d9cb6e9))

## [11.9.0-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.8.0-alpha.1...v11.9.0-alpha.1) (2026-03-02)


### Features

* bulk delete with confirmation, match tab styling to settings ([776bacb](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/776bacbf37e9997db4df9bff89e70fe20ef55084))

## [11.8.0-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.7.1-alpha.1...v11.8.0-alpha.1) (2026-03-02)


### Features

* file browser with browsable move dialog ([af13ab2](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/af13ab2719b7983d4ebe4904769ff7b1d83c9aba))

## [11.7.1-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.7.0-alpha.1...v11.7.1-alpha.1) (2026-03-02)


### Bug Fixes

* show waiting_transcode status with yellow color instead of gray ([22dd128](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/22dd1284c03b7928c41f7c975860477d4beed796))

## [11.7.0-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.6.0-alpha.1...v11.7.0-alpha.1) (2026-03-02)


### Features

* condense dashboard into unified status bar ([52d8e08](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/52d8e08c160559ff4878fa6f840044f43aa205d6))
* move drives page into settings as a tab ([f494bd7](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/f494bd7a7897993979e493aab1c76004e60226bb))
* proxy metadata requests through ARM API ([6d343f7](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/6d343f7c90522efd79fd392fb579703b06a6fcf5))


### Bug Fixes

* resolve TypeScript error and update arm_client tests ([92af79a](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/92af79a0e0a9db19cf37c4b7df36a8fbc5da1c5d))
* surface real ARM API errors instead of generic "unreachable" message ([42c8988](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/42c8988c238e347a69fcd24dacca9316ec67d6e2))

## [11.6.0-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.5.1-alpha.1...v11.6.0-alpha.1) (2026-03-01)


### Features

* per-job transcode config overrides UI ([f0638b3](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/f0638b32ce42d3e14aaa5725de2d7b7fad2b19f9))


### Bug Fixes

* prevent false 100% progress during MakeMKV scan phase ([11a52d5](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/11a52d5e6fcdb7473cf2514505e8440a9b564fee))
* read full progress file so PRGT phase messages are not missed ([c8c6e62](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/c8c6e62279dbdee357db15602f5fede439026782))

## [11.5.1-alpha.1](https://github.com/uprightbass360/automatic-ripping-machine-ui/compare/v11.5.0-alpha.1...v11.5.1-alpha.1) (2026-02-28)


### Bug Fixes

* clamp rip progress to 100% when all tracks are ripped ([92f32d1](https://github.com/uprightbass360/automatic-ripping-machine-ui/commit/92f32d1c3f4dfc553abac13efa1769698ad5fbcb))

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
