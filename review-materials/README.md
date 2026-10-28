# Final review materials

- [GUIDE_REVIEW_PPT_CONTENT.md](GUIDE_REVIEW_PPT_CONTENT.md): 12-slide working-demo
  content with speaker notes, ordinary-request demonstration, and viva questions.
- [October 28 evidence](evidence/2026-10-28/README.md): supplied screenshots of
  proactive tool invocation, preference saving, and fresh-chat memory receipts.

- [FINAL_REPORT.md](FINAL_REPORT.md): technical report with architecture, methods,
  both experiments, measured failures, limitations, and references.
- [PRESENTATION.html](PRESENTATION.html): standalone offline slide deck. Open in a
  browser; use arrow keys or on-screen buttons. Press N for speaker notes. Browser
  Print produces one slide per page for PDF export; choose landscape/no headers.
- [DEMO_SCRIPT.md](DEMO_SCRIPT.md): timed live-demo sequence and viva questions.
- `slides.json`: editable slide content and speaker notes.

Rebuild the HTML after editing slides.json:

```powershell
.\.venv\Scripts\python.exe scripts/build-review-materials.py
```

On Ubuntu/Bash, from the engine repository root:

```bash
.venv/bin/python scripts/build-review-materials.py
```

The deck is HTML, not a native PowerPoint file. It works without internet or an
installed presentation library. Add actual team names, institution, supervisor,
and required submission formatting to the report/title before academic submission.
No screenshots or teammate test results have been invented.

Automatic PDF export and visual rendering could not be verified in the restricted
tool session: Edge failed to create its Windows IPC channel. The HTML structure
and script syntax were checked. Open it in your normal browser to review its
appearance and export using Print > Save as PDF; no PDF is claimed as generated.

The main claim is commit-aware lifecycle behavior. The relevance experiment is a
negative result on its reserved partition; do not present it as a solved feature.
