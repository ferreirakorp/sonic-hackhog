export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);

  const REDIRECT_URL = env.REDIRECT_URL || "https://wise.com/";
  const LOG_URL = env.LOG_URL || "";
  const LOG_KEY = env.LOG_KEY || "";

  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const ua = request.headers.get("User-Agent") || "";
  const lang = request.headers.get("Accept-Language") || "";
  const referer = request.headers.get("Referer") || "";
  const now = new Date();
  const ts = now.toISOString();

  const visit = {
    ts, ip, ua: ua.substring(0, 200), lang, referer,
    method: request.method, path: url.pathname,
    query: url.search.slice(1),
    headers: Object.fromEntries(request.headers)
  };

  console.log(JSON.stringify({
    ts, ip, ua: ua.substring(0, 80), lang,
    method: request.method, path: url.pathname
  }));

  // Forward visit to VPS monitor (non-blocking)
  if (LOG_URL && LOG_KEY) {
    context.waitUntil(
      fetch(`${LOG_URL}/api/log`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${LOG_KEY}`
        },
        body: JSON.stringify(visit)
      }).catch(() => {})
    );
  }

  // --- daily OG auto-update (WAT / UTC+1) ---
  const wat = new Date(now.getTime() + 1 * 60 * 60 * 1000);
  const dateKey = wat.toISOString().split("T")[0];

  const dd = wat.getUTCDate().toString().padStart(2, "0");
  const mm = (wat.getUTCMonth() + 1).toString().padStart(2, "0");
  const yyyy = wat.getUTCFullYear();
  const hh = wat.getUTCHours().toString().padStart(2, "0");
  const min = wat.getUTCMinutes().toString().padStart(2, "0");

  let ogTimestamp;

  if (env.OG_STATE) {
    try {
      ogTimestamp = await env.OG_STATE.get(dateKey);
    } catch (e) {}

    if (!ogTimestamp) {
      ogTimestamp = `${dd}${mm}${yyyy}${hh}${min}`;
      try {
        await env.OG_STATE.put(dateKey, ogTimestamp, { expirationTtl: 172800 });
        console.log(JSON.stringify({
          event: "OG_DAILY_UPDATE",
          date: dateKey,
          new_og: `Comprovativo_${ogTimestamp}`,
          generated_at: ts
        }));
      } catch (e) {}
    }
  } else {
    ogTimestamp = `${dd}${mm}${yyyy}${hh}${min}`;
  }

  const ogTitle = `Comprovativo_${ogTimestamp}`;

  const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta property="og:title" content="${ogTitle}">
<meta property="og:image" content="${url.origin}/og.jpg">
<meta property="og:image:width" content="1792">
<meta property="og:image:height" content="2400">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${ogTitle}">
<meta name="twitter:image" content="${url.origin}/og.jpg">
<title>${ogTitle}</title>
<meta http-equiv="refresh" content="0;url=${REDIRECT_URL}">
</head>
<body>
<script>window.location.replace("${REDIRECT_URL}");</script>
</body>
</html>`;

  return new Response(html, {
    headers: { "Content-Type": "text/html;charset=UTF-8" }
  });
}
