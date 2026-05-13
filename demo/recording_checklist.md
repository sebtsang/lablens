# Pre-recording sanity checklist

Run through this BEFORE you hit record. Each item that fails costs you a take.

## Tech setup
- [ ] Railway deploy is live and `/health` returns ok at the public URL
- [ ] LLM env is set in Railway (`LABLENS_LLM_PROVIDER=gemini` + `GEMINI_API_KEY`, or Anthropic equivalents)
- [ ] Browser zoom is 100% (so text is sharp)
- [ ] Screen recorder is set to ≥1080p, 30fps
- [ ] Microphone test — record 5 seconds, listen back, no clipping

## Prompt Opinion setup
- [ ] Logged into a clean workspace (no leftover other-project data)
- [ ] `Patient_001_Urgent_Potassium` is uploaded and visible in the patient list
- [ ] LabLens MCP server is registered in Workspace Hub with FHIR-context box checked
- [ ] LabLens Triage Agent is configured with all 4 tools attached
- [ ] Test invocation succeeded once — confirm by reading the cached result in the launchpad

## Demo content
- [ ] Tool-calls panel toggle is **on** (so judges see the orchestration)
- [ ] Browser tabs other than Prompt Opinion are closed (no notification spillover)
- [ ] Slack/Discord/email DnD enabled
- [ ] Have the rule trace zoomed-in shot prepped (or know the keystroke to zoom)

## Script
- [ ] `demo/demo_script.md` reviewed; key phrases memorized:
  - "Three independent potassium-raising mechanisms coexisting in this patient's regimen"
  - "Same inputs always produce same outputs — deterministic rule trace"
  - "Fails safe to INSUFFICIENT_DATA"
- [ ] Stopwatch ready — target under 3:00, hard cap at 2:55 to leave buffer

## Post-recording
- [ ] Upload to YouTube as **public** (rules §4: must be publicly visible)
- [ ] Title: "LabLens — Lab Triage Agent for Agents Assemble Healthcare AI Hackathon"
- [ ] Description includes:
  - One-line pitch
  - Link to GitHub repo
  - Link to Prompt Opinion Marketplace listing
  - Hackathon: agents-assemble.devpost.com
- [ ] Verify the link works in incognito (catches private-by-default upload errors)
- [ ] Add the YouTube URL to the Devpost submission form

## Rules check (fail Stage 1 if missed)
- [ ] Video shows it functioning **inside Prompt Opinion** (not just our local code)
- [ ] No real PHI anywhere visible (every name on screen is the synthetic one)
- [ ] No third-party trademarks or copyrighted music
- [ ] Under 3 minutes
- [ ] English narration
