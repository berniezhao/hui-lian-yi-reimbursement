# Browser Authentication

## Verified scope

On 2026-09-14, agent-browser 0.22.3 successfully used a fresh HuiLianYi QR login to read the current travel form. The probe keeps credentials inside the page evaluation and returns only an allowlisted state, HTTP status and field count. It is an authentication/form-read probe, not a general API client.

Observed storage on `https://console-a2.huilianyi.com`:

- `localStorage['hly.token']`: JSON object; use `access_token` with `token_type: bearer`. The object also contains refresh metadata, but no refresh flow has been validated.
- `localStorage['hly.custom-browser-tenantId']`: decimal text; base64-encode the original text for `X-Tenant-Id`. Do not parse it as a JavaScript Number: observed tenant IDs exceed the safe integer range.

The verified request used `Accept: application/json`, `Authorization: Bearer <access_token>` and `X-Tenant-Id`, with `credentials: omit`. No cookie or browser-specific header was required for this form read. This does not establish requirements for other endpoints.

## Run the probe

1. Reuse the dedicated task session. Inspect the page first; if login is required, follow the QR procedure in [ui-and-recovery.md](ui-and-recovery.md). A session name existing is not proof that its page is authenticated.
2. Resolve the current form OID from the current workflow or verified readback; do not copy a sample OID as a universal default.
3. Run from the installed skill directory, or use the script's absolute path:

```bash
python3 scripts/browser-auth-probe.py --session hly-recover --form-oid <current-form-uuid>
```

Success exits 0 with a compact result such as:

```json
{"state":"authenticated","httpStatus":200,"fieldCount":21}
```

The script uses `agent-browser eval --stdin`, checks the exact HTTPS origin before reading storage, and permits only `GET /api/custom/forms/{UUID}`. The fetch aborts after 12 seconds, refuses redirects and checks the returned form identity and field structure. The agent-browser subprocess has a 25-second timeout. It neither navigates nor closes the session, so the caller can continue in the same browser.

Credentials are read afresh for each run. Do not export token/cookies, save authentication state, dump storage, log raw network detail, copy credentials into configuration, or put them in a checkpoint. The script captures CLI output internally and emits only allowed fields; it suppresses raw stdout/stderr and exception text on errors. These protections cover this helper; independently requested browser traces or HAR exports may contain credentials and are not needed for this flow.

## Failure handling

Non-success states exit 1:

| State | Next step |
|---|---|
| `wrong_origin` | Inspect the task page and navigate to the known HuiLianYi entry when safe; no storage was read |
| `login_required` | Inspect UI login state; obtain a fresh QR only if login is actually required |
| `unsupported_auth_format` / `storage_unavailable` | Stop credential extraction; inspect only key names/type metadata, never dump values |
| `auth_rejected` | HTTP 401/403; inspect login and access permissions before assuming expiry or requesting another QR |
| `http_error` | A different non-success HTTP status; check the selected form/business context, do not assume bad token |
| `unexpected_response` | HTTP response did not have the expected form identity/fields; do not accept it as authentication proof |
| `request_timeout` / `request_failed` | Inspect browser transport and proxy state; redirects and other fetch failures share `request_failed` |
| `browser_timeout` / `browser_unavailable` / `browser_command_failed` / `invalid_browser_output` | Inspect CLI availability/session and required local permissions; do not print raw output to diagnose credentials |

Do not manually redeem or rotate a refresh token. If the web page has refreshed its session, rerunning the probe obtains the current access token. If the session is expired, use the ordinary site login. Network-header capture is an unimplemented alternative, not a verified fallback.

A valid probe is not proof that a reimbursement was saved, submitted or correctly dated. Verify each subsequent read route in the current context, and continue business writes through the existing UI procedure until their contracts have been validated within an authorized task.
