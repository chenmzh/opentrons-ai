# 控制台使用说明 / Console guide

## 当前功能 / Available now

- 中文 / EN 切换，自动保存浏览器语言偏好；不翻译用户输入和硬件型号。
- 管理员、操作员、查看者账号。查看者只能读取；操作员可拍照；硬件导入和目录批准、账号创建仅限管理员。
- 实时查询 OT-2 健康、移液器和相机状态；界面每 20 秒更新，服务端缓存最多 5 秒。连接失败显示未知或不可用，不使用历史数据冒充在线。
- 手动添加硬件、导入 CSV/JSON、发现移液器、显式批准目录记录。所有新条目默认待审核。目录批准不代表设备已具备执行条件。
- 可选拍照、查看和下载原图。照片及拍照故障不影响目录审批或其他操作，也不会被发送给 AI。

This is the foundation milestone. No AI planning, simulation, run queue, motion controls, or experiment execution endpoints are implemented. The deck graphic is an unassigned schematic, not a detected setup. Camera settings are never changed automatically.

## 本次本机验证 / This host's verified instance

On 2026-09-14 the console was started at `https://127.0.0.1:8443`, bound only to loopback. The administrator is `admin`; its generated password is in the local, Git-ignored `.local/bootstrap-admin.txt`. A real login, pipette discovery (pending approval), and a 640×480 camera capture succeeded through the UI. Fifteen mocked backend tests and five browser tests passed. Screenshots are in `runs/ui/live-overview-zh.png` and `runs/ui/live-overview-en.png`.

This instance uses a locally generated self-signed certificate. Its SHA-256 fingerprint is `3F:E8:DC:8D:8A:22:96:81:73:97:0C:A3:23:37:F2:EF:5C:C8:78:BC:C2:99:CA:D1:FF:FC:45:B7:A2:7E:C0:8A`. Verify that fingerprint before trusting the certificate in a browser. No system trust store was modified.

LAN publication was rejected by automatic approval review because it would expose authenticated team records and camera images on the network. Only loopback serving was started. Opening `the configured LAN endpoint` to the lab network remains pending explicit approval; no firewall or forwarding configuration was changed. The current foreground server does not automatically restart after a reboot.

## 安装与启动 / Install and start

Requires Python 3.12+, Node 20.19+ and pnpm 12. On Ubuntu, install `python3.12-venv` if virtual environment creation fails.

```bash
make setup
make build
.venv/bin/python -m opentrons_ai create-admin --username admin
make run
```

The admin command prompts for a password of at least 12 characters. There is no default password. Alternatively, use `--generate` to generate a random password in `.local/bootstrap-admin.txt` with owner-only permissions; an existing user or credential file is never overwritten. Open `http://127.0.0.1:8080` on this computer.

管理员登录后，可在“团队与记录”页面为同事创建账号。密码只保存为 Argon2 哈希；会话八小时后过期。账号密码管理目前仅支持创建；忘记密码需通过后续维护流程处理，不能通过清空数据库恢复而丢弃记录。

## 局域网 HTTPS / Lab network access

LAN binding requires HTTPS. Supply a certificate trusted by your lab and its private key:

```bash
.venv/bin/python -m opentrons_ai serve --host 0.0.0.0 --port 8443 \
  --cert .local/tls/cert.pem --key .local/tls/key.pem
```

Use `https://<this-computer-LAN-IP>:8443` from other computers on the permitted lab network. The application does not open firewall rules or configure router forwarding. For local evaluation, a self-signed certificate is acceptable after checking its fingerprint; browsers will warn until the certificate is trusted. Use a lab-issued certificate for routine team deployment.

局域网访问需要同事的电脑能连接到本机端口。没有验证其他电脑的路由或实验室防火墙。不要通过公网转发此服务。

## Hardware import

CSV headers and category values are language-independent:

```csv
name,category,model,serial,notes
My plate,labware,exact_load_name,,Awaiting definition review
```

Allowed categories: `pipette`, `labware`, `tiprack`, `module`, `other`. JSON accepts an array of equivalent records, an object with an `items` array, or a single Opentrons schema-v2 labware definition. Imports are limited to 200 entries and 2 MB. Records retain their entered language. JSON definitions receive basic structural checks; this is not full geometry validation or simulation. CSV records can be catalog-approved without a definition but remain unqualified for execution.

Discover queries connected pipettes and adds previously unknown serials as pending records. It does not discover plates, tips, or liquid contents; supply those records explicitly. Import and discovery do not replace existing entries. Editing, revocation, full definition validation, and experiment qualification are later milestones.

## Persistence and configuration

Set `OT2_URL` on the server, never in the browser. Without it the console reports the robot as disconnected and makes no robot requests. The robot adapter has fixed status GET endpoints and a single camera POST endpoint. There is no arbitrary proxy or code-execution endpoint.

`OT2_DATA_DIR` defaults to the repository's `.local/` directory. This contains the SQLite database (users, sessions, hardware, captures, audit records), original JPEGs under `captures/`, and any local bootstrap credentials/certificates. It is excluded from Git. The gallery shows the most recent 100 images; older originals remain on disk. Monitor storage and back up the directory while the server is stopped, including SQLite WAL files if present. Keep backups private.

For this single-host observation milestone, SQLite transactions support a small team without requiring PostgreSQL. The full execution architecture still calls for PostgreSQL and a separately isolated robot service. These are not yet installed or enforced by this foundation implementation. Run one server process; camera capture locking and status caching are process-local. Automatic restart and nightly backup services are not installed by the application.

## Development and checks

```bash
make test                 # Mock robot; no hardware requests
make lint                 # Python and frontend formatting/static checks
make build                # TypeScript checking and production assets
pnpm --dir frontend exec playwright install chromium
make test-ui              # Browser tests with intercepted robot/API fixtures
```

Browser tests start an isolated server on loopback port 8091 and store screenshots under `runs/ui/`. For frontend development, run `make run` and `pnpm --dir frontend dev` in separate terminals; Vite proxies `/api` to the local backend. Rebuild before serving production assets.

UI translation keys live in `frontend/src/i18n.ts`. Every English key must have a Chinese entry (enforced by TypeScript). Translate application error codes at the UI, not robot IDs, scientific labels, serial numbers, or imported content. Test language switching during errors and after browser reload.
