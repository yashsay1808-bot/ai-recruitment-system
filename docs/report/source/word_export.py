import os, subprocess, tempfile, shutil


def export_pdf(docx_path, pdf_path):
    """Export a .docx to PDF with Microsoft Word (COM). Returns page count."""
    tmp = tempfile.mkdtemp()
    src = os.path.join(tmp, "in.docx")
    shutil.copy(docx_path, src)
    out = os.path.join(tmp, "out.pdf")
    ps = f'''
$ErrorActionPreference = "Stop"
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try {{
  $d = $w.Documents.Open("{src}", $false, $true)
  $d.Repaginate()
  $d.ExportAsFixedFormat("{out}", 17)
  Write-Output ("PAGES=" + $d.ComputeStatistics(2))
  $d.Close($false)
}} finally {{ $w.Quit() }}
'''
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=600)
    if res.returncode != 0 or not os.path.exists(out):
        raise RuntimeError("Word export failed: " + res.stdout + res.stderr)
    shutil.copy(out, pdf_path)
    shutil.rmtree(tmp, ignore_errors=True)
    for line in res.stdout.splitlines():
        if line.startswith("PAGES="):
            return int(line.split("=")[1])
    return None
