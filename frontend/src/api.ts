export class ApiError extends Error {
  constructor(public code: string) {
    super(code);
  }
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
  csrf = "",
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "opentrons-console",
        "X-CSRF-Token": csrf,
        ...options.headers,
      },
    });
  } catch {
    throw new ApiError("network_error");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(
      typeof body.detail === "string" ? body.detail : "unexpected_error",
    );
  }
  return response.json();
}

// Small RFC-4180-style CSV reader: quoted fields, embedded newlines, and CRLF.
export function parseCsv(text: string): Record<string, string>[] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let quoted = false;
  text = text.replace(/^\uFEFF/, "");
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') {
      if (quoted && text[i + 1] === '"') {
        field += '"';
        i++;
      } else quoted = !quoted;
    } else if (c === "," && !quoted) {
      row.push(field);
      field = "";
    } else if ((c === "\n" || c === "\r") && !quoted) {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(field);
      if (row.some(Boolean)) rows.push(row);
      row = [];
      field = "";
    } else field += c;
  }
  if (quoted) throw new ApiError("invalid_file");
  row.push(field);
  if (row.some(Boolean)) rows.push(row);
  const headers = rows.shift()?.map((h) => h.trim());
  if (
    !headers?.includes("name") ||
    !headers.includes("category") ||
    new Set(headers).size !== headers.length
  )
    throw new ApiError("invalid_file");
  return rows.map((values) => {
    if (values.length !== headers.length) throw new ApiError("invalid_file");
    return Object.fromEntries(headers.map((header, i) => [header, values[i]]));
  });
}
