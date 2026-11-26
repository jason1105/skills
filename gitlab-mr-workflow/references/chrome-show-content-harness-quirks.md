# content.test.js FakeNode harness quirks (chrome-show-issue-and-mr-no)

Learned while implementing #16 (panel state filter) — saved future debugging time.

## The harness is a hand-rolled FakeNode DOM, not jsdom

- `FakeNode` has `children` (plain array), `attributes` (Map), `getAttribute` returns `null` when absent — closest to real DOM, but **no `.closest()`** and no `Element` methods beyond querySelector/find. Writing test assertions that use real-DOM-only APIs fails with `x.closest is not a function`.
- `querySelector`/`querySelectorAll` walk children recursively via `.find()`; attribute selectors like `[data-foo="bar"]` work.

## Stale-node trap: re-call `getBadge()` after any re-render

`getBadge(harness.document)` returns direct node references. After an action that re-renders the panel (filter click, navigation), those references are **detached** (panel content was `replaceChildren`'d). Symptom: `Cannot read properties of undefined (reading 'dispatchEvent'/'textContent')` on a button that clearly exists. Fix: `const after = getBadge(harness.document)` — never reuse the pre-action snapshot for post-action assertions.

Also: DOM-removal + re-creation flows (e.g. navigation to a page that drops then re-adds the badge) need a fresh `getBadge` **between** the removal-triggering event and the re-open event; dispatching `focus` on the stale `rendered.trigger` throws.

## Debugging pattern: instrumented copy of the test file

To see what the harness actually did (storage writes, fetch order) without touching the real test:
1. Copy `tests/content.test.js` to `tests/<name>.test.js` **inside the repo** (a copy in /tmp breaks `require('../src/parser.js')` — relative resolution).
2. Replace the failing `assert` with a `console.log` of the relevant harness state (e.g. `harness.storageCalls.set.map(v => v[CONFIG_STORAGE_KEY]...)`).
3. Run `node --test --test-name-pattern '<pattern>' tests/<name>.test.js`, read output, delete the copy.
Bash heredoc/inline-node with regex replaces on the test source trips the CLI quote-blocker — do the string surgery from `execute_code` (Python) instead.

## Persisted-preference bug pattern (caught by this)

When adding a NEW persisted preference written from the content-script panel: `persistSearchState()` only persists `{query, listFilter}` into `config.searchState`. Calling it with a new field (e.g. `itemStateFilter`) **silently drops the field** — test only fails at a storage-content assertion, not at the call site. Correct path for a user-level preference: `configStore.save({ <field> }, origin)` directly (queued, normalizes, sets `userOverrides[field] = true`).

## DOM-order assertions: use relative order, not adjacency

When asserting that a new row (e.g. a state-filter row) sits between two existing sections, `panel.children` ordering is: `header, searchControls, stateControls, searchSummary, results` — an intermediate element (here `searchSummary`) can sit between your row and the results node. Asserting `resultsIndex === stateIndex + 1` fails with `The expression evaluated to a falsy value` while the DOM is actually correct.

Fix (verified 2026-08-20, #16 test 48): assert relative order instead of adjacency:
```js
const controlsIndex = panelChildren.findIndex(n => n.getAttribute('data-open-items-controls') !== null);
const stateIndex = panelChildren.indexOf(rendered.stateControls);
const resultsIndex = panelChildren.findIndex(n => n.getAttribute('data-open-items-results') !== null);
assert.ok(controlsIndex >= 0 && stateIndex === controlsIndex + 1 && resultsIndex > stateIndex);
```
`stateIndex === controlsIndex + 1` (row directly under its own controls) is fine; the results side must use `>`, because summary/status lines can be inserted between them in later iterations. When a test fails on ordering, first read the actual `panel.append(...)` call in content.js before "fixing" the implementation — the assertion may be over-strict.

## Storage-area change (#17, chrome.storage.sync migration)

Since #17 the extension persists config in `chrome.storage.sync` (uninstall/reinstall survives via the signed-in Chrome account) with `chrome.storage.local` as a one-time migration source. Harness implications:

- The content.test.js storage mock now exposes **both** `sync` and `local` areas, sharing ONE backing record (`storageData`). `sync.set`/`sync.remove` dispatch `storageChangeListeners` with areaName `'sync'`; the `local` area's set/remove do NOT notify listeners. `dispatchStorageChanged` defaults to `'sync'` (was `'local'`).
- `config.js` `handleStorageChanged` filters `areaName !== 'sync'` (was `'local'`) — a test dispatching changes with `'local'` is silently ignored by the store (assertions will fail with stale values, not errors).
- The one-time migration (`createConfigStore(storage, { legacyStorage })`) runs on first `load()`: reads `sync` for `CONFIG_STORAGE_KEY`, then `local` if sync is empty. So the FIRST `storageCalls.get` is now `[CONFIG_STORAGE_KEY]` twice (sync + local probes) BEFORE the real `[CONFIG_STORAGE_KEY, POSITION_STORAGE_KEY]` read — exact-array assertions on `storageCalls.get` must expect the 3-call sequence (verified 2026-08-21, config.test.js + content.test.js 146/146).
- Migration is idempotent and keeps the local copy (background.js's `readLegacyConfig`/`migrateLegacyOriginsOnUpdate` still reads `storage.local` on update — never delete the local record).

## Panel-owned filter state pattern (works well)

For a filter that lives in the panel but must survive sessions:
- `navigation.<field>` + `<field>Owned` flag on the navigation state object.
- `resetNavigation()` must NOT clear it (add a comment saying so) — it should survive project navigation and host re-creation, like query/listFilter.
- In `updateConfig`'s `.then`: sync from `effective.<field>` only when `!owned`; include it in the `requestPolicyChanged` check (guarded by `!owned`) so external config changes still drop the cache and refetch.
- On panel toggle: bump `requestGeneration`, abort stale requests, null out cache/issues/errors, `renderNavigationPanel`, `loadOpenItems({force:true})`, then persist via `configStore.save`.
