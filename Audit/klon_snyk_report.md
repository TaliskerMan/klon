# Klon Snyk Security Scan Report

## Scope and limitations

This report records the output of automated Snyk scans (SAST + open-source
dependency analysis). **A clean Snyk result is not a clean bill of health.**
Snyk looks for known-vulnerable dependencies and a fixed set of insecure code
patterns; it does **not** understand klon's threat model, which is dominated by
*correct-but-destructive* behaviour — writing `dd` to the wrong block device is
catastrophic yet contains no "vulnerability" a scanner would flag.

The findings below should be read alongside the manual assessment
(`klon_Assessment_and_Path_to_Production.md`), which identified real defects
(broken backup-to-image, missing destructive-write guards, unverified ISO
downloads, and more) that automated scanning did not and could not surface.

## Scan Results

### 1. Snyk Code Scan (SAST)
- **Result**: `0` vulnerabilities found.
- **Interpretation**: No known insecure-code *patterns* were matched. Privileged
  commands are invoked via array-form `subprocess`/`pkexec` (no shell string),
  which removes the shell-injection surface. This is necessary but not
  sufficient: the dangerous operations here are legitimate `dd`/`sgdisk` writes
  whose safety depends on *which device* they target — logic a SAST tool does
  not evaluate.

### 2. Snyk Open Source (SCA)
- **Result**: `0` known-vulnerable dependencies found.
- **Interpretation**: The direct dependencies (`PyGObject`, `requests`) carried
  no known CVEs at scan time. Re-run on each dependency bump; a clean result is
  a point-in-time snapshot, not a guarantee.

## Conclusion

Automated scanning found no known-pattern or known-CVE issues. The project's
actual risk is controlled by the destructive-write safety guards
(`src/klon/backend/safety.py`) and their tests (`tests/test_safety.py`), and by
the ISO checksum verification — none of which are validated by these scans.
Treat this report as one input among several, not as sign-off.
