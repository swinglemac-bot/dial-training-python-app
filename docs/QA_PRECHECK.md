# QA Precheck Runbook

This project includes a practical QA bundle for catching common release issues before shipping.

## Scripts

Node requirement for Playwright web checks:
- use Node `20.x` to match the Expo project engine
- if you run the QA commands on the wrong Node version, the Playwright web startup will now fail early with a clear message

### `npm run qa:preflight`
Runs:
- `npm run lint`
- `npm run typecheck`
- `npm run test:e2e:smoke`

Use this during normal development when you want a fast confidence check that:
- the repo still lints cleanly
- TypeScript is still valid
- the app can boot and render a visible screen in the web target

### `npm run qa:full`
Runs:
- `npm run lint`
- `npm run typecheck`
- `npm run qa:knip`
- `npm run test:e2e`

Use this before merging or shipping when you want stronger regression coverage.

This catches:
- lint issues
- type issues
- obvious unused-code drift detected by `knip`
- startup/render failures in the Playwright target
- obvious navigation or screen regressions covered by the E2E suite

### `npm run qa:ci`
Runs:
- `npm run qa:full`
- `npm run verify`

Use this as the strongest repo-level preflight before release or CI gating.

This adds the existing `verify` step so the server-side verification path is also checked.

## What these checks catch well

These checks are best at catching:
- app startup failures in the web test target
- broken imports or TypeScript regressions
- lint regressions
- obvious navigation failures
- some unresponsive-button regressions when covered by Playwright flows
- broken screen rendering for major routes already covered by tests

## What these checks do not catch

These checks do **not** guarantee detection of every issue, especially:
- all native-only iPhone or Android bugs
- all TestFlight-only or release-build-only layout issues
- device-specific safe-area or keyboard bugs
- intermittent network/service issues
- subtle animation, gesture, or performance problems

## Recommended workflow

### During development
- run `npm run qa:preflight`

### Before merging or shipping
- run `npm run qa:full`

### Before a real release
- run `npm run qa:ci`
- then do manual device checks on the highest-risk flows

## Manual checks still recommended before shipping

Run these manually on device before release:
- cold app launch
- sign in / sign out
- first-run access flow
- Today screen primary action
- Coach input + send flow
- one workout start / log / results loop
- PT / Recovery / Plan navigation
- bottom navigation and floating shell controls on smaller phones
- at least one iPhone-sized device and one Android-sized device if available

## Smoke test note

The smoke test uses a safe minimal selector assumption:
- on load, the app should show either the signed-out access screen or a signed-in app shell

The test checks for one visible anchor text:
- `Member Access`
- `Today`
- or `DIALED`

That keeps the smoke test broad and resilient instead of tying it to fragile internal selectors.
