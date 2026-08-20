/*
  CLOUDFLARE WORKER - proxy para OpenRouter

  A CHAVE DO OPENROUTER NÃO FICA NESTE ARQUIVO.
  Crie um Secret no Cloudflare chamado:
    OPENROUTER_API_KEY

  Crie também uma variável comum:
    ALLOWED_ORIGIN = https://SEU-USUARIO.github.io
  ou, se o site for um project page:
    https://SEU-USUARIO.github.io

  Observação:
  Origin contém apenas esquema + host, sem /nome-do-repositorio.
*/

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";

function corsHeaders(origin, allowedOrigin) {
  const allowed = origin && allowedOrigin && origin === allowedOrigin;
  return {
    "Access-Control-Allow-Origin": allowed ? origin : allowedOrigin || "null",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
    "Content-Type": "application/json; charset=utf-8"
  };
}

function json(body, status, origin, allowedOrigin) {
  return new Response(JSON.stringify(body), {
    status,
    headers: corsHeaders(origin, allowedOrigin)
  });
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const allowedOrigin = env.ALLOWED_ORIGIN || "";

    if (request.method === "OPTIONS") {
      if (!allowedOrigin || origin !== allowedOrigin) {
        return json({ error: "Origin não permitida." }, 403, origin, allowedOrigin);
      }
      return new Response(null, {
        status: 204,
        headers: corsHeaders(origin, allowedOrigin)
      });
    }

    if (request.method !== "POST") {
      return json({ error: "Use POST." }, 405, origin, allowedOrigin);
    }

    // Impede que terceiros usem seu Worker a partir de outros sites.
    if (!allowedOrigin || origin !== allowedOrigin) {
      return json({ error: "Origin não permitida." }, 403, origin, allowedOrigin);
    }

    if (!env.OPENROUTER_API_KEY) {
      return json({ error: "OPENROUTER_API_KEY não configurada no Worker." }, 500, origin, allowedOrigin);
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: "JSON inválido." }, 400, origin, allowedOrigin);
    }

    const model =
      typeof body.model === "string" && body.model.length <= 120
        ? body.model
        : "openrouter/free";

    const systemPrompt =
      typeof body.systemPrompt === "string"
        ? body.systemPrompt.slice(0, 12000)
        : "";

    const incoming = Array.isArray(body.messages) ? body.messages : [];

    // Limites simples para reduzir abuso/custo.
    const messages = incoming
      .slice(-30)
      .filter(m => ["user", "assistant"].includes(m?.role) && typeof m?.content === "string")
      .map(m => ({
        role: m.role,
        content: m.content.slice(0, 4000)
      }));

    if (!messages.length) {
      return json({ error: "Nenhuma mensagem válida." }, 400, origin, allowedOrigin);
    }

    const temperature = Math.min(1.5, Math.max(0, Number(body.temperature ?? 0.85)));
    const max_tokens = Math.min(900, Math.max(32, Number(body.maxTokens ?? 450)));

    const payload = {
      model,
      messages: [
        ...(systemPrompt ? [{ role: "system", content: systemPrompt }] : []),
        ...messages
      ],
      temperature,
      max_tokens
    };

    try {
      const upstream = await fetch(OPENROUTER_URL, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${env.OPENROUTER_API_KEY}`,
          "Content-Type": "application/json",
          "HTTP-Referer": allowedOrigin,
          "X-Title": "Julia AI Chat"
        },
        body: JSON.stringify(payload)
      });

      const text = await upstream.text();

      // Repassa o JSON do OpenRouter ao frontend.
      return new Response(text, {
        status: upstream.status,
        headers: corsHeaders(origin, allowedOrigin)
      });

    } catch (err) {
      return json(
        { error: "Falha ao acessar OpenRouter.", detail: String(err?.message || err) },
        502,
        origin,
        allowedOrigin
      );
    }
  }
};
