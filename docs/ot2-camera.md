# Capturing OT-2 Camera Pictures

Verified locally on 2026-09-14 with an OT-2 running robot software `26.6.0`. Requires Bash, curl, and USB Ethernet connectivity. No protocol upload or robot movement is needed.

## Check connectivity and camera status

Run from the repository root:

```bash
: "${OT2_URL:?Set OT2_URL locally before connecting}"
curl --noproxy '*' --fail --silent --show-error --max-time 15 \
  -H 'Opentrons-Version: 2' "$OT2_URL/health"
curl --noproxy '*' --fail --silent --show-error --max-time 15 \
  -H 'Opentrons-Version: 2' "$OT2_URL/camera"
```

The header selects HTTP API version 2, not the Python protocol API. Omitting it returned HTTP 422. `--noproxy '*'` sends local robot traffic directly.

## Enable still-image capture if disabled

The camera initially reported all three flags as `false`. The following request enabled still capture while retaining the observed streaming and error-recovery settings:

```bash
curl --noproxy '*' --fail --silent --show-error --max-time 15 \
  -X POST -H 'Opentrons-Version: 2' -H 'Content-Type: application/json' \
  --data '{"data":{"cameraEnabled":true,"liveStreamEnabled":false,"errorRecoveryCameraEnabled":false}}' \
  "$OT2_URL/camera"
```

All three fields are required by this robot's schema. Read the current flags first; preserve their values if they differ from this example. The final verified state was `cameraEnabled: true`, `liveStreamEnabled: false`, `errorRecoveryCameraEnabled: false`. The camera was left enabled; persistence across reboot was not tested.

## Capture and save a picture

```bash
mkdir -p runs/camera
capture_path="runs/camera/ot2-$(date -u +%Y%m%dT%H%M%S-%N).jpg"
curl --noproxy '*' --fail --silent --show-error \
  --connect-timeout 5 --max-time 45 \
  -X POST -H 'Opentrons-Version: 2' \
  --dump-header "${capture_path%.jpg}.headers" \
  --output "$capture_path" "$OT2_URL/camera/picture" \
  && file "$capture_path"
```

Repeat for additional pictures. The endpoint needs no request body. Successful requests returned HTTP 200, `Content-Type: image/jpg`, and 640×480 JPEG images in about two seconds. Inspect the saved image to verify the scene; an HTTP success alone does not establish image quality. If curl fails, any partial output should not be treated as a successful capture.

## Recorded results and troubleshooting

- Both [capture-01.jpg](../runs/camera/capture-01.jpg) and [capture-02.jpg](../runs/camera/capture-02.jpg) were downloaded and visually inspected. They show an oblique view of the numbered deck. These files and response headers are local artifacts excluded from Git by the existing `runs/` rule.
- HTTP 422 with `Cannot take photo, camera is disabled.` was resolved by enabling the camera above.
- In the agent sandbox, direct connection failed; the same request worked with approved host network access. Distinguish sandbox restrictions from robot connectivity failures.
- The robot's response clock reported 2026-09-11 while the host reported 2026-09-14. Use host UTC for capture filenames; clock synchronization was not changed.
- For firmware-specific differences, inspect `GET /openapi.json` with the version header. A copy from this robot is saved locally at `runs/camera/openapi.json`.

Reference: [Opentrons HTTP API](https://docs.opentrons.com/http/api_reference.html). The enablement request was checked against this robot's own OpenAPI schema, since published documentation can differ from installed software.
