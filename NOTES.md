# Project Notes

## Connection configuration

Set `OT2_URL` locally for your robot. Actual network addresses, adapter settings,
device identifiers and robot run identifiers are excluded from this publication.
Historical success records below do not establish current connectivity.

## Camera Capture — 2026-09-14

- Health check confirmed the tested OT-2 running software `26.6.0`.
- Enabled the previously disabled still camera using `POST /camera`; streaming and error-recovery recording remain disabled.
- Captured and visually checked two 640×480 JPEGs in `runs/camera/` using `POST /camera/picture` with `Opentrons-Version: 2`.
- The camera remains enabled. No motion or protocol execution commands were sent.
- Repeatable commands and troubleshooting: [OT-2 camera method](docs/ot2-camera.md).
- Robot HTTP timestamps lagged the host date; use host capture timestamps until synchronization is investigated.

## Bilingual Console — 2026-09-14

- Foundation dashboard implemented with Chinese/English switching, local team accounts, hardware catalog approval, robot status, and optional camera records.
- Live UI login, pipette discovery, and a 640×480 capture passed. Discovered equipment remains pending catalog approval.
- Started on `https://127.0.0.1:8443` for local access only; LAN publication needs explicit approval after automatic review rejected the all-interface binding.
- Credentials, database, certificate keys, and new photos are under Git-ignored `.local/`. See [console setup](docs/dashboard.md).
- AI experiment generation and execution are not connected to the dashboard; the camera never drives automatic decisions.
