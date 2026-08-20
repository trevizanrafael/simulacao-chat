# Julia AI Chat — GitHub Pages + OpenRouter

## Estrutura do GitHub Pages

Coloque no repositório:

```text
/
├─ index.html
├─ julia-config.js
└─ assets/
   └─ julia.jpg
```

A foto deve se chamar `julia.jpg` e ficar em `assets/julia.jpg`.
Se quiser outro nome, altere `photo` dentro de `julia-config.js`.

## IMPORTANTE: chave OpenRouter

NUNCA coloque a chave dentro do `index.html`, `julia-config.js`, GitHub Actions
que injete a chave no JavaScript final, ou qualquer outro arquivo servido pelo Pages.

O navegador recebe esses arquivos e o segredo fica visível.

Use o Cloudflare Worker de `worker.js`.

## Cloudflare Worker — caminho rápido

1. Entre no Cloudflare Dashboard.
2. Vá em Workers & Pages.
3. Crie um Worker.
4. Abra o editor do Worker.
5. Substitua o código pelo conteúdo de `worker.js`.
6. Salve/deploy.

### Secret da API

No Worker, crie um Secret:

Nome:
`OPENROUTER_API_KEY`

Valor:
sua chave do OpenRouter.

### Origin permitida

Crie uma variável comum:

Nome:
`ALLOWED_ORIGIN`

Valor, por exemplo:
`https://seuusuario.github.io`

IMPORTANTE: Origin NÃO inclui `/nome-do-repositorio`.

7. Copie a URL `https://....workers.dev`.
8. Abra `julia-config.js`.
9. Troque:

```js
apiUrl: "https://SEU-WORKER.workers.dev"
```

pela URL real.

## GitHub Pages

1. Crie/abra seu repositório.
2. Envie `index.html`, `julia-config.js` e a pasta `assets`.
3. Settings → Pages.
4. Deploy from a branch.
5. Branch: `main`, pasta `/ (root)`.
6. Salve.

## Configuração da personalidade

Edite somente `julia-config.js`.

Os principais campos são:

- `name`
- `photo`
- `model`
- `temperature`
- `systemPrompt`
- `initialMessages`

O `systemPrompt` é a base que você pediu para montar do seu jeito.

## Segurança

O Worker limita:
- origem do site (CORS)
- histórico recebido
- tamanho de cada mensagem
- tokens máximos

Para um site público com tráfego real, vale adicionar rate limiting/autenticação,
pois CORS sozinho não é uma barreira absoluta contra chamadas automatizadas.
