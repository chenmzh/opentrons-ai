import {
  StrictMode,
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  Box,
  Camera,
  Check,
  CheckCircle2,
  ChevronRight,
  CircuitBoard,
  ClipboardList,
  FlaskConical,
  Globe2,
  ImageIcon,
  LayoutDashboard,
  LogOut,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Upload,
  Users,
  X,
} from "lucide-react";
import { api, ApiError, parseCsv } from "./api";
import { en, zh, type Key, type Language } from "./i18n";
import "./style.css";

type User = {
  username: string;
  role: "admin" | "operator" | "viewer";
  csrf: string;
};
type Hardware = {
  id: string;
  name: string;
  category: "pipette" | "labware" | "tiprack" | "module" | "other";
  model: string;
  serial: string;
  notes: string;
  status: "pending" | "approved";
  revision: number;
  definition: object | null;
  approved_by: string | null;
};
type Capture = {
  id: string;
  created_at: string;
  username: string;
  width: number;
  height: number;
};
type RobotStatus = {
  connected: boolean;
  checked_at: string;
  address: string;
  health: { name: string; api_version: string } | null;
  pipettes: Record<
    string,
    { name: string | null; model: string | null; id: string | null }
  > | null;
  modules: { modules: unknown[] } | null;
  camera: { cameraEnabled: boolean } | null;
};
type Audit = {
  id: number;
  created_at: string;
  username: string;
  action: string;
  detail: string;
};
type Page = "overview" | "hardware" | "camera" | "team";

function Dialog({
  title,
  children,
  close,
}: {
  title: string;
  children: ReactNode;
  close: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={close}
      onClick={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <div className="dialog-head">
        <h2>{title}</h2>
        <button
          className="icon-button"
          onClick={close}
          aria-label="Close / 关闭"
        >
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}

function App() {
  const [lang, setLang] = useState<Language>(() => {
    try {
      return localStorage.getItem("ot2-language") === "en" ? "en" : "zh";
    } catch {
      return "zh";
    }
  });
  const t = (key: Key) => (lang === "zh" ? zh : en)[key];
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);
  const [page, setPage] = useState<Page>("overview");
  const [robot, setRobot] = useState<RobotStatus | null>(null);
  const [hardware, setHardware] = useState<Hardware[]>([]);
  const [captures, setCaptures] = useState<Capture[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [audit, setAudit] = useState<Audit[]>([]);
  const [error, setError] = useState<Key | null>(null);
  const [notice, setNotice] = useState<Key | null>(null);
  const [busy, setBusy] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [approval, setApproval] = useState<Hardware | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [selectedPhoto, setSelectedPhoto] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);
  const csrf = user?.csrf ?? "";
  const canEdit = user?.role === "admin";
  const canCapture = user?.role === "admin" || user?.role === "operator";

  useEffect(() => {
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
    document.title =
      lang === "zh"
        ? "Opentrons AI · 实验室控制台"
        : "Opentrons AI · Lab console";
    try {
      localStorage.setItem("ot2-language", lang);
    } catch {
      /* Private browser storage. */
    }
  }, [lang]);
  useEffect(() => {
    api<User>("/me")
      .then(setUser)
      .catch(() => {})
      .finally(() => setChecking(false));
  }, []);

  const handleError = useCallback((e: unknown) => {
    const code = e instanceof ApiError ? e.code : "unexpected_error";
    setError(code in en ? (code as Key) : "unexpected_error");
    if (code === "unauthorized") setUser(null);
  }, []);
  const refreshRobot = useCallback(async () => {
    setRefreshing(true);
    try {
      setRobot(await api<RobotStatus>("/robot"));
    } catch (e) {
      setRobot(null);
      handleError(e);
    } finally {
      setRefreshing(false);
    }
  }, [handleError]);
  const loadRecords = useCallback(async () => {
    const results = await Promise.allSettled([
      api<Hardware[]>("/hardware").then(setHardware),
      api<Capture[]>("/captures").then(setCaptures),
    ]);
    results.forEach((result) => {
      if (result.status === "rejected") handleError(result.reason);
    });
  }, [handleError]);
  const loadTeam = useCallback(async () => {
    const results = await Promise.allSettled([
      api<User[]>("/users").then(setUsers),
      api<Audit[]>("/audit").then(setAudit),
    ]);
    results.forEach((result) => {
      if (result.status === "rejected") handleError(result.reason);
    });
  }, [handleError]);
  useEffect(() => {
    if (!user) return;
    void refreshRobot();
    void loadRecords();
    const interval = window.setInterval(() => void refreshRobot(), 20000);
    return () => window.clearInterval(interval);
  }, [user, refreshRobot, loadRecords]);
  useEffect(() => {
    if (page === "team" && canEdit) void loadTeam();
  }, [page, canEdit, loadTeam]);

  async function action(name: string, work: () => Promise<void>) {
    setBusy(name);
    setError(null);
    setNotice(null);
    try {
      await work();
    } catch (e) {
      handleError(e);
    } finally {
      setBusy("");
    }
  }
  function stamp(value: string) {
    return new Intl.DateTimeFormat(lang === "zh" ? "zh-CN" : "en-GB", {
      dateStyle: "medium",
      timeStyle: "medium",
    }).format(new Date(value));
  }
  async function takePicture() {
    await action("capture", async () => {
      const photo = await api<Capture>("/captures", { method: "POST" }, csrf);
      setSelectedPhoto(photo.id);
      await loadRecords();
    });
  }
  async function importFile(file: File) {
    await action("import", async () => {
      if (file.size > 2_000_000) throw new ApiError("file_too_large");
      const content = await file.text();
      let items: unknown;
      try {
        if (file.name.toLowerCase().endsWith(".csv")) items = parseCsv(content);
        else {
          const data = JSON.parse(content);
          if (data.schemaVersion === 2)
            items = [
              {
                name: data.metadata?.displayName ?? data.parameters?.loadName,
                category: data.parameters?.isTiprack ? "tiprack" : "labware",
                model: data.parameters?.loadName,
                definition: data,
              },
            ];
          else items = Array.isArray(data) ? data : data.items;
        }
        if (!Array.isArray(items) || !items.length) throw new Error();
      } catch {
        throw new ApiError("invalid_file");
      }
      await api(
        "/hardware/import",
        { method: "POST", body: JSON.stringify({ items }) },
        csrf,
      );
      await loadRecords();
      setNotice("imported");
    });
  }

  const languageSwitch = (
    <div className="language-switch" role="group" aria-label={t("language")}>
      <Globe2 size={15} />
      <button aria-pressed={lang === "zh"} onClick={() => setLang("zh")}>
        中文
      </button>
      <span>/</span>
      <button aria-pressed={lang === "en"} onClick={() => setLang("en")}>
        EN
      </button>
    </div>
  );
  const alerts = (
    <>
      {error && (
        <div className="alert error" role="alert">
          {t(error)}
          <button onClick={() => setError(null)} aria-label="关闭 / Dismiss">
            <X size={16} />
          </button>
        </div>
      )}
      {notice && (
        <div className="alert success" role="status">
          <Check size={16} />
          {t(notice)}
        </div>
      )}
    </>
  );
  const photo =
    captures.find((item) => item.id === selectedPhoto) ?? captures[0];
  const imagePath = (id: string) => `/api/v1/captures/${id}/image`;
  const cameraEmpty = (
    <div className="camera-empty">
      <div className="empty-icon">
        <Camera size={30} strokeWidth={1.3} />
      </div>
      <h3>{t("noPhoto")}</h3>
      <p>{t("noPhotoNote")}</p>
    </div>
  );

  if (checking)
    return (
      <div className="loading-screen">
        <FlaskConical size={32} />
        <p>{t("sessionChecking")}</p>
      </div>
    );
  if (!user)
    return (
      <div className="login-layout">
        <section className="login-art">
          <div className="brand">
            <div className="brand-icon">
              <FlaskConical size={25} />
            </div>
            <div>
              Opentrons AI<small>{t("console")}</small>
            </div>
          </div>
          <div className="login-art-body">
            <div className="eyebrow">PRECISION / POSSIBILITY</div>
            <h1>{t("loginTitle")}</h1>
            <p>{t("phaseNote")}</p>
            <div className="art-deck" aria-hidden="true">
              {Array.from({ length: 12 }, (_, i) => (
                <div key={i}>
                  {String(i + 1).padStart(2, "0")}
                  <span>
                    ••••
                    <br />
                    ••••
                  </span>
                </div>
              ))}
            </div>
            <div className="login-features">
              {(
                ["loginFeature1", "loginFeature2", "loginFeature3"] as Key[]
              ).map((k) => (
                <span key={k}>
                  <CheckCircle2 size={16} />
                  {t(k)}
                </span>
              ))}
            </div>
          </div>
          <small>OT-2 / LAB OPERATIONS</small>
        </section>
        <section className="login-panel">
          <div className="login-language">{languageSwitch}</div>
          <form
            className="login-form"
            onSubmit={(event) => {
              event.preventDefault();
              const data = new FormData(event.currentTarget);
              void action("login", async () => {
                const result = await api<User>("/login", {
                  method: "POST",
                  body: JSON.stringify(Object.fromEntries(data)),
                });
                setUser(result);
              });
            }}
          >
            <span className="section-label">{t("lab")}</span>
            <h2>{t("login")}</h2>
            <p>{t("loginSubtitle")}</p>
            {alerts}
            <label>
              {t("username")}
              <input
                name="username"
                autoComplete="username"
                required
                maxLength={64}
                autoFocus
              />
            </label>
            <label>
              {t("password")}
              <input
                name="password"
                type="password"
                autoComplete="current-password"
                required
                maxLength={256}
              />
            </label>
            <button className="primary full" disabled={!!busy}>
              {t(busy === "login" ? "loginBusy" : "login")}
              <ArrowRight size={17} />
            </button>
            <small>{t("loginNote")}</small>
          </form>
          <div className="login-footer">
            <ShieldCheck size={15} />
            {t("readOnly")} · {t("noExecution")}
          </div>
        </section>
      </div>
    );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <FlaskConical size={23} />
          </div>
          <div>
            Opentrons AI<small>{t("console")}</small>
          </div>
        </div>
        <span className="nav-label">{t("workspace")}</span>
        <nav>
          {(
            [
              ["overview", LayoutDashboard],
              ["hardware", Box],
              ["camera", Camera],
              ...(canEdit ? [["team", Users]] : []),
            ] as const
          ).map(([name, Icon]) => (
            <button
              key={name as string}
              className={page === name ? "nav-item active" : "nav-item"}
              onClick={() => {
                setPage(name as Page);
                setError(null);
                setNotice(null);
              }}
            >
              <Icon size={19} />
              <span>{t(name as Page)}</span>
              {page === name && <ChevronRight size={16} />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="phase-card">
            <ShieldCheck size={20} />
            <strong>{t("phase")}</strong>
            <p>{t("noExecution")}</p>
          </div>
          <div className="profile">
            <div className="avatar">
              {user.username.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <strong>{user.username}</strong>
              <small>{t(user.role)}</small>
            </div>
            <button
              className="icon-button"
              title={t("logout")}
              aria-label={t("logout")}
              onClick={() =>
                void action("logout", async () => {
                  await api("/logout", { method: "POST" }, csrf);
                  setUser(null);
                  setPage("overview");
                  setHardware([]);
                  setCaptures([]);
                })
              }
            >
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            {t("lab")}
            <ChevronRight size={14} />
            <strong>{t(page)}</strong>
          </div>
          <div className="topbar-right">
            <span className="observation">
              <span className="status-dot" />
              {t("readOnly")}
            </span>
            {languageSwitch}
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <div className="section-label">OT-2 / {t(page)}</div>
              <h1>
                {t(
                  page === "overview"
                    ? "welcome"
                    : page === "hardware"
                      ? "hardwareTitle"
                      : page === "camera"
                        ? "cameraTitle"
                        : "teamTitle",
                )}
              </h1>
              <p>
                {t(
                  page === "overview"
                    ? "subtitle"
                    : page === "hardware"
                      ? "hardwareSubtitle"
                      : page === "camera"
                        ? "cameraSubtitle"
                        : "teamSubtitle",
                )}
              </p>
            </div>
            {page === "overview" && (
              <button
                className="secondary"
                onClick={() => void refreshRobot()}
                disabled={refreshing}
              >
                <RefreshCw size={16} className={refreshing ? "spin" : ""} />
                {t(refreshing ? "refreshing" : "refresh")}
              </button>
            )}
          </div>
          {alerts}

          {page === "overview" && (
            <>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-label">
                    {t("robot")}
                    <Activity size={18} />
                  </div>
                  <strong className={robot?.connected ? "green" : ""}>
                    {t(
                      robot
                        ? robot.connected
                          ? "connected"
                          : "offline"
                        : "unknown",
                    )}
                  </strong>
                  <small>
                    {robot?.health?.name ?? "OT-2"} · {robot?.address ?? "—"}
                  </small>
                </div>
                <div className="stat-card">
                  <div className="stat-label">
                    {t("instruments")}
                    <CircuitBoard size={18} />
                  </div>
                  <strong>
                    {robot?.pipettes
                      ? Object.values(robot.pipettes).filter((p) => p?.model)
                          .length
                      : "—"}
                    <span>/ 2</span>
                  </strong>
                  <small>
                    {t("left")} / {t("right")}
                  </small>
                </div>
                <div className="stat-card">
                  <div className="stat-label">
                    {t("approvedHardware")}
                    <ShieldCheck size={18} />
                  </div>
                  <strong>
                    {hardware.filter((h) => h.status === "approved").length}
                    <span>/ {hardware.length}</span>
                  </strong>
                  <small>{t("catalogOnly")}</small>
                </div>
                <div className="stat-card">
                  <div className="stat-label">
                    {t("referenceImages")}
                    <ImageIcon size={18} />
                  </div>
                  <strong>{captures.length}</strong>
                  <small>{t("optionalCamera")}</small>
                </div>
              </div>
              <div className="overview-grid">
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>{t("deck")}</h2>
                      <p>{t("deckNote")}</p>
                    </div>
                    <span className="tag">OT-2</span>
                  </div>
                  <div className="deck-grid">
                    {[10, 11, 12, 7, 8, 9, 4, 5, 6, 1, 2, 3].map((slot) => (
                      <div
                        key={slot}
                        className={
                          slot === 12 ? "deck-slot trash" : "deck-slot"
                        }
                      >
                        <strong>{String(slot).padStart(2, "0")}</strong>
                        {slot === 12 ? (
                          <>
                            <Box size={22} />
                            <small>{t("trash")}</small>
                          </>
                        ) : (
                          <>
                            <div className="slot-mark" />
                            <small>{t("unassigned")}</small>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                  <div className="mounts">
                    {(["left", "right"] as const).map((mount) => (
                      <div key={mount}>
                        <span className="mount-icon">
                          <CircuitBoard size={18} />
                        </span>
                        <div>
                          <small>{t(mount)}</small>
                          <strong>
                            {robot?.pipettes
                              ? (robot.pipettes[mount]?.name ?? t("emptyMount"))
                              : t("unknown")}
                          </strong>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
                <div className="right-column">
                  <section className="panel photo-panel">
                    <div className="panel-heading">
                      <h2>{t("latestPhoto")}</h2>
                      <button
                        className="text-button"
                        onClick={() => setPage("camera")}
                      >
                        {t("openCamera")}
                        <ArrowRight size={15} />
                      </button>
                    </div>
                    {captures[0] ? (
                      <div className="preview-image">
                        <img
                          src={imagePath(captures[0].id)}
                          alt={t("imageAlt")}
                        />
                        <span>{t("notLive")}</span>
                      </div>
                    ) : (
                      cameraEmpty
                    )}
                    <div className="photo-panel-footer">
                      <small>
                        {captures[0]
                          ? stamp(captures[0].created_at)
                          : t("optionalCamera")}
                      </small>
                      {canCapture && (
                        <button
                          className="secondary compact"
                          disabled={!!busy}
                          onClick={() => void takePicture()}
                        >
                          <Camera size={15} />
                          {t(busy === "capture" ? "capturing" : "capture")}
                        </button>
                      )}
                    </div>
                  </section>
                  <div className="calibration-note">
                    <ShieldCheck size={21} />
                    <div>
                      <strong>{t("calibration")}</strong>
                      <p>{t("calibrationNote")}</p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bottom-info">
                <div>
                  <ClipboardList size={20} />
                  <div>
                    <strong>{t("future")}</strong>
                    <p>{t("futureNote")}</p>
                  </div>
                </div>
                <span>
                  {t("lastChecked")}:{" "}
                  {robot?.checked_at ? stamp(robot.checked_at) : "—"}
                </span>
              </div>
            </>
          )}

          {page === "hardware" && (
            <>
              <div className="toolbar">
                <div className="search-field">
                  <Search size={17} />
                  <input
                    aria-label={t("search")}
                    placeholder={t("search")}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                  />
                </div>
                <select
                  aria-label={t("status")}
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                >
                  {(["all", "pending", "approved"] as const).map((k) => (
                    <option key={k} value={k}>
                      {t(k)}
                    </option>
                  ))}
                </select>
                {canEdit && (
                  <div className="toolbar-actions">
                    <button
                      className="secondary"
                      disabled={!!busy}
                      onClick={() =>
                        void action("discover", async () => {
                          await api(
                            "/hardware/discover",
                            { method: "POST" },
                            csrf,
                          );
                          await loadRecords();
                          setNotice("discovered");
                        })
                      }
                    >
                      <RefreshCw size={16} />
                      {t(busy === "discover" ? "discovering" : "discover")}
                    </button>
                    <button
                      className="secondary"
                      disabled={!!busy}
                      onClick={() => fileInput.current?.click()}
                    >
                      <Upload size={16} />
                      {t("import")}
                    </button>
                    <input
                      ref={fileInput}
                      type="file"
                      accept=".csv,.json"
                      hidden
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) void importFile(file);
                        e.target.value = "";
                      }}
                    />
                    <button
                      className="primary"
                      onClick={() => setShowAdd(true)}
                    >
                      <Plus size={17} />
                      {t("addHardware")}
                    </button>
                  </div>
                )}
              </div>
              <p className="help-text">{t("importHelp")}</p>
              <section className="panel table-panel">
                {!hardware.length ? (
                  <div className="empty-state">
                    <div className="empty-icon">
                      <Box size={30} />
                    </div>
                    <h2>{t("noHardware")}</h2>
                    <p>{t("noHardwareNote")}</p>
                    {canEdit && (
                      <button
                        className="primary"
                        onClick={() => setShowAdd(true)}
                      >
                        <Plus size={17} />
                        {t("addHardware")}
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          {(
                            [
                              "name",
                              "category",
                              "model",
                              "status",
                              "actions",
                            ] as Key[]
                          ).map((k) => (
                            <th key={k}>{t(k)}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {hardware
                          .filter(
                            (h) =>
                              (filter === "all" || h.status === filter) &&
                              `${h.name} ${h.model} ${h.serial}`
                                .toLowerCase()
                                .includes(query.toLowerCase()),
                          )
                          .map((h) => (
                            <tr key={h.id}>
                              <td>
                                <strong>{h.name}</strong>
                                <small>{h.serial || "—"}</small>
                                {h.notes && <small>{h.notes}</small>}
                              </td>
                              <td>{t(h.category)}</td>
                              <td>
                                {h.model || "—"}
                                {["labware", "tiprack"].includes(
                                  h.category,
                                ) && (
                                  <small>
                                    {t(
                                      h.definition
                                        ? "definitionAttached"
                                        : "noDefinition",
                                    )}
                                  </small>
                                )}
                              </td>
                              <td>
                                <span className={`badge ${h.status}`}>
                                  {h.status === "approved" && (
                                    <Check size={13} />
                                  )}
                                  {t(h.status)}
                                </span>
                                {h.approved_by && (
                                  <small>
                                    {t("approvedBy")}: {h.approved_by}
                                  </small>
                                )}
                              </td>
                              <td>
                                {h.status === "pending" && canEdit ? (
                                  <button
                                    className="text-button"
                                    onClick={() => setApproval(h)}
                                  >
                                    {t("approve")}
                                    <ArrowRight size={14} />
                                  </button>
                                ) : (
                                  "—"
                                )}
                              </td>
                            </tr>
                          ))}
                        {!hardware.some(
                          (h) =>
                            (filter === "all" || h.status === filter) &&
                            `${h.name} ${h.model} ${h.serial}`
                              .toLowerCase()
                              .includes(query.toLowerCase()),
                        ) && (
                          <tr>
                            <td colSpan={5}>{t("noMatches")}</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </>
          )}

          {page === "camera" && (
            <>
              <div className="camera-toolbar">
                <span
                  className={`badge ${robot?.camera?.cameraEnabled ? "approved" : "pending"}`}
                >
                  <Camera size={14} />
                  {t(
                    robot?.camera
                      ? robot.camera.cameraEnabled
                        ? "cameraEnabled"
                        : "cameraDisabled"
                      : "cameraUnknown",
                  )}
                </span>
                {canCapture && (
                  <button
                    className="primary"
                    disabled={!!busy}
                    onClick={() => void takePicture()}
                  >
                    <Camera size={17} />
                    {t(busy === "capture" ? "capturing" : "capture")}
                  </button>
                )}
              </div>
              <div className="camera-layout">
                <section className="panel camera-view">
                  {photo ? (
                    <>
                      <div className="camera-large">
                        <img src={imagePath(photo.id)} alt={t("imageAlt")} />
                        <span className="image-label">{t("notLive")}</span>
                      </div>
                      <div className="image-info">
                        <div>
                          <strong>{stamp(photo.created_at)}</strong>
                          <small>
                            {photo.width} × {photo.height} · JPEG ·{" "}
                            {t("capturedBy")} {photo.username}
                          </small>
                        </div>
                        <a
                          className="secondary"
                          href={imagePath(photo.id)}
                          download={`ot2-${photo.id}.jpg`}
                        >
                          <ArrowDownToLine size={16} />
                          {t("download")}
                        </a>
                      </div>
                    </>
                  ) : (
                    cameraEmpty
                  )}
                </section>
                <section className="panel gallery">
                  <div className="panel-heading">
                    <div>
                      <h2>{t("photos")}</h2>
                      <p>{t("imagesLocal")}</p>
                    </div>
                    <span className="tag">{captures.length}</span>
                  </div>
                  {captures.length ? (
                    captures.map((c) => (
                      <button
                        className={`gallery-item ${photo?.id === c.id ? "selected" : ""}`}
                        key={c.id}
                        onClick={() => setSelectedPhoto(c.id)}
                      >
                        <img src={imagePath(c.id)} alt="" />
                        <div>
                          <strong>{stamp(c.created_at)}</strong>
                          <small>
                            {c.width} × {c.height} · {c.username}
                          </small>
                        </div>
                      </button>
                    ))
                  ) : (
                    <p className="gallery-empty">{t("noData")}</p>
                  )}
                </section>
              </div>
            </>
          )}

          {page === "team" && canEdit && (
            <>
              <div className="team-grid">
                <section className="panel">
                  <div className="panel-heading">
                    <h2>{t("members")}</h2>
                    <Users size={19} />
                  </div>
                  <div className="member-list">
                    {users.map((member) => (
                      <div className="member" key={member.username}>
                        <div className="avatar">
                          {member.username.slice(0, 2).toUpperCase()}
                        </div>
                        <strong>{member.username}</strong>
                        <span className="tag">{t(member.role)}</span>
                      </div>
                    ))}
                  </div>
                </section>
                <section className="panel">
                  <div className="panel-heading">
                    <h2>{t("createUser")}</h2>
                    <Plus size={19} />
                  </div>
                  <form
                    className="account-form"
                    onSubmit={(e) => {
                      e.preventDefault();
                      const form = e.currentTarget;
                      const data = Object.fromEntries(new FormData(form));
                      void action("user", async () => {
                        await api(
                          "/users",
                          { method: "POST", body: JSON.stringify(data) },
                          csrf,
                        );
                        form.reset();
                        await loadTeam();
                        setNotice("saved");
                      });
                    }}
                  >
                    <label>
                      {t("username")}
                      <input
                        name="username"
                        required
                        pattern="[a-zA-Z0-9_.\-]+"
                        maxLength={64}
                        autoComplete="off"
                      />
                    </label>
                    <label>
                      {t("password")}
                      <input
                        name="password"
                        type="password"
                        required
                        minLength={12}
                        maxLength={256}
                        autoComplete="new-password"
                      />
                      <small>{t("passwordHelp")}</small>
                    </label>
                    <label>
                      {t("role")}
                      <select name="role" defaultValue="operator">
                        {(["operator", "viewer", "admin"] as const).map(
                          (role) => (
                            <option key={role} value={role}>
                              {t(role)}
                            </option>
                          ),
                        )}
                      </select>
                    </label>
                    <button className="primary" disabled={!!busy}>
                      {t("createUser")}
                      <ArrowRight size={16} />
                    </button>
                  </form>
                </section>
              </div>
              <section className="panel table-panel audit-panel">
                <div className="panel-heading">
                  <h2>{t("activity")}</h2>
                  <button
                    className="text-button"
                    onClick={() => void loadTeam()}
                  >
                    <RefreshCw size={16} />
                    {t("refresh")}
                  </button>
                </div>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>{t("time")}</th>
                        <th>{t("user")}</th>
                        <th>{t("event")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {audit.map((entry) => (
                        <tr key={entry.id}>
                          <td>{stamp(entry.created_at)}</td>
                          <td>{entry.username}</td>
                          <td>
                            {t(`event_${entry.action}` as Key) ?? entry.action}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}
        </main>
        <footer className="app-footer">
          <span>
            Opentrons AI <span className="footer-separator">/</span>{" "}
            {t("phase")}
          </span>
          <span>{t("optionalCamera")}</span>
        </footer>
      </div>
      {showAdd && (
        <Dialog title={t("addHardware")} close={() => setShowAdd(false)}>
          <form
            className="hardware-form"
            onSubmit={(e: FormEvent<HTMLFormElement>) => {
              e.preventDefault();
              const data = Object.fromEntries(new FormData(e.currentTarget));
              void action("save", async () => {
                await api(
                  "/hardware",
                  { method: "POST", body: JSON.stringify(data) },
                  csrf,
                );
                await loadRecords();
                setShowAdd(false);
                setNotice("saved");
              });
            }}
          >
            <label>
              {t("name")}
              <input name="name" required maxLength={120} autoFocus />
            </label>
            <label>
              {t("category")}
              <select name="category">
                {(
                  ["labware", "tiprack", "pipette", "module", "other"] as const
                ).map((k) => (
                  <option key={k} value={k}>
                    {t(k)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              {t("model")}
              <input name="model" maxLength={120} />
            </label>
            <label>
              {t("serial")}
              <input name="serial" maxLength={120} />
            </label>
            <label className="span-two">
              {t("notes")}
              <textarea name="notes" maxLength={1000} rows={3} />
            </label>
            <p className="help-text span-two">{t("catalogOnly")}</p>
            {error && (
              <p className="inline-error span-two" role="alert">
                {t(error)}
              </p>
            )}
            <div className="dialog-actions span-two">
              <button
                type="button"
                className="secondary"
                onClick={() => setShowAdd(false)}
              >
                {t("cancel")}
              </button>
              <button className="primary" disabled={!!busy}>
                {t("save")}
              </button>
            </div>
          </form>
        </Dialog>
      )}
      {approval && (
        <Dialog title={t("approveTitle")} close={() => setApproval(null)}>
          <div className="approval-body">
            <strong>{approval.name}</strong>
            <p>{t("approveNote")}</p>
            {error && (
              <p className="inline-error" role="alert">
                {t(error)}
              </p>
            )}
            <div className="dialog-actions">
              <button className="secondary" onClick={() => setApproval(null)}>
                {t("cancel")}
              </button>
              <button
                className="primary"
                disabled={!!busy}
                onClick={() =>
                  void action("approve", async () => {
                    await api(
                      `/hardware/${approval.id}/approve`,
                      {
                        method: "POST",
                        body: JSON.stringify({ revision: approval.revision }),
                      },
                      csrf,
                    );
                    await loadRecords();
                    setApproval(null);
                    setNotice("saved");
                  })
                }
              >
                {t("confirm")}
              </button>
            </div>
          </div>
        </Dialog>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
