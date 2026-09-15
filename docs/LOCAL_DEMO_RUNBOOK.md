# Local VEDA-BORDER demo runbook

Run from the repository root.

1. Start the backend:

```bash
cd services/api
PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000
```

2. In another terminal start the frontend:

```bash
npm --prefix apps/web run dev
```

3. Open `http://localhost:3000`.

4. In **Officer Mode**, choose a controlled fixture such as **Poor Capture Quality** or **DOB Contradiction**, then select **Check document**. The top result must show **OVERALL RESULT**, **What is the issue?**, **NEXT STEP**, and **Evidence Coverage**.

5. Choose an external entry. The upload card identifies it as an **External Dataset Sample** and the filename is resolved through the curated MIDV allowlist. The result should show the backend states `PASS`, `FAIL`, `SUSPICIOUS`, `UNAVAILABLE`, or `NOT_APPLICABLE` without inventing a pass.

6. Verify the result sections: submitted image, visible fields, visible-vs-machine-readable comparison, checks, and unavailable evidence. A missing comparison face must read **Not needed** / `NOT_APPLICABLE`.

7. Select **Developer Mode** to inspect lane payloads, hard gates, coverage, evidence graph, and service readiness. This is the diagnostic view; it is intentionally more technical.

8. Use **Recent cases** and reopen a case. If the original image was not retained, the result must say **Image preview unavailable for this saved case** rather than displaying the current upload.

9. Stop both terminals with `Ctrl-C`.

FastRouter is optional. When disabled or unreachable the result must show **AI Reasoning: UNAVAILABLE** (or **DEGRADED**) and **Deterministic Explanation Active**. The core outcome must remain unchanged. Configure only the backend environment; never place the key in frontend variables.

The curated MIDV subset is under `data/external_demo/MIDV2020`. Docker, when available, should mount external samples read-only; the API still applies the manifest allowlist.
