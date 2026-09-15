#!/usr/bin/env python3
"""Validate HuiLianYi browser authentication without exporting credentials."""

import argparse
import json
import re
import subprocess
import sys


STATES = {
    "authenticated", "wrong_origin", "login_required", "storage_unavailable",
    "unsupported_auth_format", "auth_rejected", "http_error",
    "unexpected_response", "request_timeout", "request_failed",
    "browser_timeout", "browser_unavailable", "browser_command_failed",
    "invalid_browser_output",
}


def browser_script(form_oid):
    # The only substituted value is a validated UUID encoded as a JSON literal.
    return """(async () => {
  const result = (state, extra = {}) => ({state, ...extra});
  if (location.origin !== 'https://console-a2.huilianyi.com')
    return result('wrong_origin');
  let raw, tenant, auth;
  try {
    raw = localStorage.getItem('hly.token');
    tenant = localStorage.getItem('hly.custom-browser-tenantId');
  } catch { return result('storage_unavailable'); }
  if (!raw || !tenant) return result('login_required');
  try { auth = JSON.parse(raw); }
  catch { return result('unsupported_auth_format'); }
  if (!auth || typeof auth.access_token !== 'string' ||
      !auth.access_token || /[\\r\\n]/.test(auth.access_token) ||
      typeof auth.token_type !== 'string' ||
      auth.token_type.toLowerCase() !== 'bearer' || !/^\\d+$/.test(tenant))
    return result('unsupported_auth_format');
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch('/api/custom/forms/' + FORM_OID, {
      method: 'GET',
      headers: {Accept: 'application/json',
        Authorization: 'Bearer ' + auth.access_token,
        'X-Tenant-Id': btoa(tenant)},
      credentials: 'omit', redirect: 'error', signal: controller.signal
    });
    const httpStatus = response.status;
    if (httpStatus === 401 || httpStatus === 403)
      return result('auth_rejected', {httpStatus});
    if (!response.ok) return result('http_error', {httpStatus});
    let body;
    try { body = await response.json(); }
    catch { return result('unexpected_response', {httpStatus}); }
    if (!body || body.formOID !== FORM_OID ||
        !Array.isArray(body.customFormFields))
      return result('unexpected_response', {httpStatus});
    return result('authenticated', {
      httpStatus, fieldCount: body.customFormFields.length
    });
  } catch {
    return result(controller.signal.aborted ? 'request_timeout' : 'request_failed');
  } finally { clearTimeout(timer); }
})()""".replace("FORM_OID", json.dumps(form_oid))


def probe(session, form_oid):
    try:
        completed = subprocess.run(
            ["agent-browser", "--session", session, "--json", "eval", "--stdin"],
            input=browser_script(form_oid), text=True, capture_output=True, timeout=25,
        )
    except subprocess.TimeoutExpired:
        return {"state": "browser_timeout"}
    except OSError:
        return {"state": "browser_unavailable"}
    # Never forward raw stdout/stderr, even on an error.
    if completed.returncode:
        return {"state": "browser_command_failed"}
    try:
        envelope = json.loads(completed.stdout)
        if envelope.get("success") is not True:
            return {"state": "browser_command_failed"}
        data = envelope["data"]["result"]
        state = data["state"]
        if state not in STATES:
            raise ValueError("unsupported state")
        safe = {"state": state}
        if type(data.get("httpStatus")) is int and 100 <= data["httpStatus"] <= 599:
            safe["httpStatus"] = data["httpStatus"]
        if type(data.get("fieldCount")) is int and data["fieldCount"] >= 0:
            safe["fieldCount"] = data["fieldCount"]
        return safe
    except (ValueError, TypeError, KeyError, AttributeError):
        return {"state": "invalid_browser_output"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, help="Existing dedicated agent-browser session")
    parser.add_argument("--form-oid", required=True, help="Current known form UUID")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", args.session):
        parser.error("invalid session name")
    if not re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", args.form_oid):
        parser.error("form-oid must be a UUID")
    result = probe(args.session, args.form_oid.lower())
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["state"] == "authenticated" else 1


if __name__ == "__main__":
    sys.exit(main())
