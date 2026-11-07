const domains = Object.freeze({
  douyin: "douyin.com",
  xiaohongshu: "xiaohongshu.com",
  zhihu: "zhihu.com",
  tiktok: "tiktok.com",
});
const format = "browser-session-handoff-v1";
const encode = new TextEncoder();
const decode = new TextDecoder();
const maxBytes = 2_000_000;

const toBase64 = (bytes) => btoa(Array.from(bytes, (byte) => String.fromCharCode(byte)).join(""));
const fromBase64 = (value) => Uint8Array.from(atob(value), (char) => char.charCodeAt(0));

async function deriveKey(password, salt) {
  const material = await crypto.subtle.importKey("raw", encode.encode(password), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", hash: "SHA-256", salt, iterations: 600_000 },
    material, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"],
  );
}

const parameters = (site, iv) => ({
  name: "AES-GCM", iv, additionalData: encode.encode(`${format}:${site}`),
});

export async function encrypt(site, password, cookies) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const key = await deriveKey(password, salt);
  const ciphertext = await crypto.subtle.encrypt(parameters(site, iv), key, encode.encode(JSON.stringify(cookies)));
  return { format, site, salt: toBase64(salt), iv: toBase64(iv), ciphertext: toBase64(new Uint8Array(ciphertext)) };
}

export async function decrypt(site, password, bundle) {
  if (bundle.format !== format || bundle.site !== site) throw new Error("请选择同一平台的加密包。");
  const salt = fromBase64(bundle.salt);
  const iv = fromBase64(bundle.iv);
  if (salt.length !== 16 || iv.length !== 12) throw new Error("加密包格式无效。");
  const key = await deriveKey(password, salt);
  const plaintext = await crypto.subtle.decrypt(parameters(site, iv), key, fromBase64(bundle.ciphertext));
  return JSON.parse(decode.decode(plaintext));
}

export function cookieSettings(site, cookies, storeId) {
  if (!Object.hasOwn(domains, site) || !Array.isArray(cookies) || !cookies.length) {
    throw new Error("加密包没有该平台的可用 Cookie。");
  }
  const root = domains[site];
  const now = Date.now() / 1000;
  return cookies.map((cookie) => {
    const host = cookie.domain?.replace(/^\./, "");
    if (!host || !/^[a-z0-9.-]+$/i.test(host) ||
        (host !== root && !host.endsWith(`.${root}`)) ||
        typeof cookie.name !== "string" || typeof cookie.value !== "string" ||
        typeof cookie.hostOnly !== "boolean" || typeof cookie.httpOnly !== "boolean" ||
        typeof cookie.secure !== "boolean" || !cookie.path?.startsWith("/") ||
        !["no_restriction", "lax", "strict", "unspecified"].includes(cookie.sameSite) ||
        cookie.partitionKey) {
      throw new Error("加密包含不支持或超出该平台范围的 Cookie。");
    }
    if (cookie.expirationDate !== undefined &&
        (!Number.isFinite(cookie.expirationDate) || cookie.expirationDate <= now)) {
      return null;
    }
    return {
      url: `https://${host}/`,
      name: cookie.name,
      value: cookie.value,
      path: cookie.path,
      secure: cookie.secure,
      httpOnly: cookie.httpOnly,
      sameSite: cookie.sameSite,
      storeId,
      ...(cookie.hostOnly ? {} : { domain: cookie.domain }),
      ...(cookie.expirationDate === undefined ? {} : { expirationDate: cookie.expirationDate }),
    };
  }).filter(Boolean);
}

async function currentStore() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const store = (await chrome.cookies.getAllCookieStores()).find((item) => item.tabIds.includes(tab?.id));
  if (!store || tab.incognito) throw new Error("请在普通 Chrome 窗口操作。");
  return store.id;
}

async function transfer(operation) {
  const site = document.querySelector("#site").value;
  const password = document.querySelector("#password").value;
  const status = document.querySelector("#status");
  const buttons = Array.from(document.querySelectorAll("button"));
  if (password.length < 16) {
    status.textContent = "请输入至少 16 字符的随机口令。";
    return;
  }
  const file = document.querySelector("#file").files[0];
  if (operation === "import" && (!file || file.size > maxBytes)) {
    status.textContent = "请选择小于 2 MB 的加密包。";
    return;
  }
  buttons.forEach((button) => { button.disabled = true; });
  status.textContent = "处理中…";
  try {
    const domain = domains[site];
    if (!await chrome.permissions.request({ origins: [`https://*.${domain}/*`] })) {
      status.textContent = "Chrome 未授予该平台的访问权限。";
      return;
    }
    const storeId = await currentStore();
    const existing = await chrome.cookies.getAll({ domain, storeId });
    if (operation === "export") {
      const cookies = existing.filter((cookie) => !cookie.partitionKey);
      if (!cookies.length) throw new Error("当前 Chrome 配置没有该平台可导出的 Cookie。");
      const bundle = await encrypt(site, password, cookies);
      const data = JSON.stringify(bundle);
      if (data.length > maxBytes) throw new Error("加密包超过大小限制。");
      const verified = await decrypt(site, password, JSON.parse(data));
      if (JSON.stringify(verified) !== JSON.stringify(cookies)) {
        throw new Error("加密包回读校验失败。");
      }
      const url = URL.createObjectURL(new Blob([data], { type: "application/json" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `${site}.encrypted.json`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 10_000);
      status.textContent = "已生成该平台加密包。请检查 Chrome 下载列表。";
    } else {
      if (existing.length) {
        status.textContent = "该站点已有 Cookie。请在尚未访问该平台的专用配置中导入。";
        return;
      }
      const cookies = await decrypt(site, password, JSON.parse(await file.text()));
      const settings = cookieSettings(site, cookies, storeId);
      if (!settings.length) throw new Error("包内 Cookie 已过期。");
      let restored = 0;
      for (const item of settings) {
        try {
          const result = await chrome.cookies.set(item);
          if (result?.value === item.value) restored += 1;
        } catch {
          // Browser errors can contain cookie values.
        }
      }
      status.textContent = `写入 ${restored}/${settings.length} 条。请打开平台后台核对登录和账号。`;
    }
  } catch {
    status.textContent = operation === "export"
      ? "导出失败。请确认当前配置已登录该平台，且 Chrome 已授权。"
      : "导入失败。请核对平台、口令、文件及 Chrome 权限。";
  } finally {
    document.querySelector("#password").value = "";
    buttons.forEach((button) => { button.disabled = false; });
  }
}

if (typeof document !== "undefined") {
  document.querySelector("#export").addEventListener("click", () => void transfer("export"));
  document.querySelector("#import").addEventListener("click", () => void transfer("import"));
}
