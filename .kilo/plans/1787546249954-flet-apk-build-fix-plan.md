# CBRE Break – Flet APK Build Fix Plan

## Root Cause
Flet 0.86.5 generates an `android/gradle.properties` with `org.gradle.jvmargs=-Xmx8G` and `-XX:MaxMetaspaceSize=4G` (12 GB total). That exceeds both GitHub Actions runners (~7 GB) and the local machine (3.4 GB), so the Gradle daemon gets OOM-killed → exit code 2 after ~2 minutes.

## Goal
Reduce Gradle memory footprint so the APK build completes successfully on GitHub Actions, then publish via F-Droid Pre-Distributions.

## Decisions
- Use `pyproject.toml` `[tool.flet.android.gradle_properties]` to override the generated Gradle memory settings.
- Keep Flet 0.86.5 (no downgrade needed).
- Keep bundle ID `de.cbre.breakapp`.
- Keep GitHub Actions as primary build path; retain `build_apk.sh` as fallback.

## Tasks

### 1. Add `pyproject.toml`
Create `/home/dosenkohl/Dokumente/CBRE-BREAK/pyproject.toml` with:
```toml
[project]
name = "cbre-break"
version = "1.0.0"
description = "CBRE Break - Break-Bestellungen verwalten"
dependencies = ["flet==0.86.5"]

[tool.flet]
org = "de.cbre"
product = "CBRE Break"

[tool.flet.android.gradle_properties]
"org.gradle.jvmargs" = "-Xmx3G -XX:MaxMetaspaceSize=1G"
"org.gradle.workers.max" = 2
```

### 2. Update GitHub Actions workflow
Update `.github/workflows/build-apk.yml`:
- Remove manual `GRADLE_OPTS` env var (it is ignored by the generated Gradle project).
- Keep `--no-compile-packages` to reduce memory pressure.
- Add a step to show the generated `build/flutter/android/gradle.properties` for debugging.

### 3. Trigger and validate
- Push to `main` to start the workflow.
- Verify the workflow completes with `success`.
- Download the `app-release.apk` artifact.
- Confirm APK size is reasonable (~50–100 MB expected for Flet apps).

### 4. Post-build
- Create GitHub Release `v1.0` with the APK.
- Update `metadata/de.cbre.breakapp.yml` URLs to point to the release asset.
- Prepare MR to `fdroiddata`.

## Risks
- Even with reduced memory, the build may still fail if other dependencies are missing.
- Flet 0.86.5 on Ubuntu-latest may have other untested assumptions.
- If this fails again, fallback options: self-hosted runner with more RAM, or a cloud Mac/Windows builder.

## Validation
- GitHub Actions run status = `success`.
- Artifact `cbre-break-apk` exists and is a valid APK.
- `unzip -l` on the APK shows expected contents.
