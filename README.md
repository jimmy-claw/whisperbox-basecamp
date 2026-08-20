# WhisperBox — public Basecamp catalog

Public [Logos Basecamp](https://logos.co) package repository for **WhisperBox**:
privacy-first, end-to-end-encrypted forms that sync peer-to-peer over Waku.
No server sees the questions or the answers — responses are ECIES-sealed to
the form creator and only the creator can decrypt them.

It ships three modules:

| Package | Version | Type | Built by |
|---|---|---|---|
| `whisperbox` | 0.1.0 | `ui_qml` (view) | nix in CI (public source) |
| `whisperbox_core` | 0.1.0 | `core` (append-only event-log engine + ECIES + sync) | nix in CI (public source) |
| `delivery_module` | 0.2.3 | `core` (Reliable-Channels transport) | **vendored** (see below) |

Source: [`vpavlin/whisperbox-logos`](https://github.com/vpavlin/whisperbox-logos)
(public). Verified E2E on two real Basecamp 0.2.3 instances before publishing
(form created in client A appeared in B; B answered from the UI; A decrypted
B's sealed response over the wire — both instances converged).

## Add this repo in Basecamp

In Basecamp → package manager → *Add repository*, paste the catalog identity URL:

```
https://raw.githubusercontent.com/jimmy-claw/whisperbox-basecamp/main/logos-repo.json
```

Basecamp reads `indexUrl` from that file, fetches
[`index.json`](https://raw.githubusercontent.com/jimmy-claw/whisperbox-basecamp/main/index.json),
and downloads each `.lgx` from its GitHub Release asset URL. Install
`delivery_module` and `whisperbox_core` first (the `whisperbox` view depends
on `whisperbox_core`, which depends on `delivery_module`).

## Test plan (two clients, E2E)

The interesting behavior needs **two Basecamp instances** (two machines, or two
profiles/instances on one machine — each instance gets its own identity):

1. **Client A:** open WhisperBox → *New form* → add a question (e.g. "Where for
   team lunch?" with radio options) → create it. Copy the share URI (or scan
   the QR).
2. **Client B:** open WhisperBox → *Join by URI* → paste the share URI. The form
   should appear (this is the Waku delivery path — may take a few seconds; if
   the mesh is sparse, wait up to ~30s or toggle the app closed/open).
3. **Client B:** answer the question and submit. Client B now shows "answered"
   for that form (it can't read other answers — they're sealed to A).
4. **Client A:** open the form → the response table shows B's decrypted answer.
   You can *confirm* it (the confirmation is a public, deterministic marker) and
   export responses to CSV.
5. Optional: close Client B, restart it → it should catch up its state from the
   log (cold-start convergence).

Privacy notes: form questions are public (needed for discovery); only answers
are E2E-encrypted. Each client has its own on-device identity keypair; there is
no central server and no way to link a respondent's answer to their device
beyond what the creator can already see.

## How distribution works

- Every `.lgx` is a **GitHub Release asset**. `index.json` points at the stable
  `https://github.com/jimmy-claw/whisperbox-basecamp/releases/download/<tag>/<file>.lgx`
  URLs and carries each package's `sha256`, `size`, and `rootHash` (from the
  embedded `manifest.json`) so Basecamp can verify the download.
- The catalog itself (`logos-repo.json`, `index.json`) is served straight from
  `raw.githubusercontent.com` on the `main` branch — no server to run.

## CI — `.github/workflows/release-catalog.yml`

Trigger by pushing a tag `catalog-v*`, or via *Run workflow* (workflow_dispatch,
with a `tag` input). The workflow:

1. builds `whisperbox_core` and the `whisperbox` view reproducibly with **nix**
   (`nix build .#whisperbox_core .#whisperbox` from the PUBLIC source repo),
2. attaches those two plus the vendored `delivery_module` `.lgx` to a
   **GitHub Release** under the tag,
3. regenerates `index.json` against the release-asset URLs and commits it to
   `main`.

No secrets needed — the WhisperBox source repo is public; only the built-in
`GITHUB_TOKEN` is used.

## Vendored `delivery_module`

`vendor/logos-delivery_module-module-v0.2.3.lgx` is **not** reproducible from a
public nix build (hand-repacked channels build, same artifact KYM ships). It is
vendored here and attached to releases as-is. To refresh it, rebuild
out-of-band and replace the vendored file before tagging.
