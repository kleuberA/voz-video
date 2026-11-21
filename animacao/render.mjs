#!/usr/bin/env node
/**
 * Renderiza um Short quadro a quadro (determinístico) e codifica com ffmpeg. Não precisa de
 * servidor à parte: o script sobe um servidor estático local na raiz do repositório.
 *
 *   node animacao/render.mjs stills videos/short-ep06-black-friday A 0,1.5,3,8,14,20,26,30
 *   node animacao/render.mjs video  videos/short-ep06-black-friday A
 *   node animacao/render.mjs encode videos/short-ep06-black-friday A
 *   node animacao/render.mjs tudo   videos/short-ep06-black-friday A       # video + encode
 *
 * Tempos: usa <ep>/timing[-B].json (da narração, montar_audio.py); sem ele, o timing-provisorio
 * (tempo_provisorio.py) e o vídeo sai marcado RASCUNHO.
 * Áudio: <ep>/audio[-B]/mix.wav e mix_sem_trilha.wav, se existirem; sem eles, sai mudo.
 * Saídas na pasta do episódio: estuda-leges-<id>[-B][-rascunho].mp4, -sem-trilha.mp4 e -capa.png.
 * Requer Playwright (require('playwright')) e ffmpeg.
 */
import { spawn } from "node:child_process";
import { createReadStream, existsSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { createRequire } from "node:module";
import path from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const RAIZ = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const PALCO = { width: 432, height: 768, scale: 2.5 }; // 1080×1920
const TIPOS = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".png": "image/png", ".woff2": "font/woff2" };

function servidor() {
    return new Promise((ok) => {
        const s = createServer((req, res) => {
            const rel = decodeURIComponent(new URL(req.url, "http://x").pathname);
            const arq = path.join(RAIZ, path.normalize(rel));
            if (!arq.startsWith(RAIZ) || !existsSync(arq) || statSync(arq).isDirectory()) {
                res.writeHead(404).end();
                return;
            }
            res.writeHead(200, { "content-type": TIPOS[path.extname(arq)] ?? "application/octet-stream", "cache-control": "no-store" });
            if (req.method === "HEAD") res.end();
            else createReadStream(arq).pipe(res);
        });
        s.listen(0, "127.0.0.1", () => ok(s));
    });
}

function run(cmd, args) {
    return new Promise((ok, falha) => {
        const p = spawn(cmd, args, { stdio: ["ignore", "inherit", "inherit"] });
        p.on("exit", (c) => (c === 0 ? ok() : falha(new Error(`${cmd} saiu com ${c}`))));
    });
}

async function abrir(ep, variante) {
    const srv = await servidor();
    const porta = srv.address().port;
    const browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: PALCO.width, height: PALCO.height }, deviceScaleFactor: PALCO.scale });
    page.on("pageerror", (e) => console.error("pageerror:", e.message));
    page.on("console", (m) => m.type() === "error" && console.error("console:", m.text()));
    await page.goto(`http://127.0.0.1:${porta}/animacao/pagina.html?ep=${encodeURIComponent(ep)}&variante=${variante}`, { waitUntil: "load" });
    await page.waitForFunction(() => Boolean(window.__video), null, { timeout: 30000 });
    const info = await page.evaluate(() => ({ fps: window.__video.fps, quadros: window.__video.quadros, duracao: window.__video.duracao, timing: window.__video.timing, capa: window.__video.capa }));
    return { srv, browser, page, info };
}

const clip = { x: 0, y: 0, width: PALCO.width, height: PALCO.height };
const idDo = (ep) => JSON.parse(readFileSync(path.join(RAIZ, ep, "config.json"), "utf8")).animacao;
const rascunho = (info) => info.timing.includes("provisorio");

async function stills(ep, variante, tempos) {
    const { srv, browser, page, info } = await abrir(ep, variante);
    const dir = path.join(RAIZ, "animacao", "out", idDo(ep), "stills");
    mkdirSync(dir, { recursive: true });
    for (const t of tempos) {
        await page.evaluate((n) => window.__video.setFrame(n), Math.round(t * info.fps));
        const arq = path.join(dir, `${variante}-${t.toFixed(2).padStart(5, "0")}.png`);
        await page.screenshot({ path: arq, clip });
        console.log(arq);
    }
    await browser.close();
    srv.close();
}

async function video(ep, variante) {
    const { srv, browser, page, info } = await abrir(ep, variante);
    const dir = path.join(RAIZ, "animacao", "out", idDo(ep));
    mkdirSync(dir, { recursive: true });
    const mkv = path.join(dir, `quadros-${variante}.mkv`);
    console.log(`${ep} ${variante}: ${info.quadros} quadros (${info.duracao} s) com ${info.timing}`);
    // mezanino praticamente sem perdas: as versões finais saem dele
    const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(info.fps), "-c:v", "png", "-i", "-",
        "-c:v", "libx264", "-preset", "ultrafast", "-qp", "0", "-pix_fmt", "yuv444p", mkv], { stdio: ["pipe", "inherit", "inherit"] });
    const ini = Date.now();
    for (let n = 0; n < info.quadros; n++) {
        await page.evaluate((q) => window.__video.setFrame(q), n);
        const png = await page.screenshot({ type: "png", clip });
        if (!ff.stdin.write(png)) await new Promise((ok) => ff.stdin.once("drain", ok));
        if (n % 150 === 0) console.log(`  quadro ${n}/${info.quadros} (${((Date.now() - ini) / 1000).toFixed(0)} s)`);
    }
    ff.stdin.end();
    await new Promise((ok) => ff.on("exit", ok));
    await browser.close();
    srv.close();
    console.log(mkv);
    return info;
}

async function encode(ep, variante, info) {
    if (!info) {
        const a = await abrir(ep, variante);
        info = a.info;
        await a.browser.close();
        a.srv.close();
    }
    const id = idDo(ep);
    const mkv = path.join(RAIZ, "animacao", "out", id, `quadros-${variante}.mkv`);
    const suf = (variante === "A" ? "" : `-${variante}`) + (rascunho(info) ? "-rascunho" : "");
    const base = path.join(RAIZ, ep, `estuda-leges-${id}${suf}`);
    const audioDir = path.join(RAIZ, ep, variante === "A" ? "audio" : `audio-${variante}`);
    const v = ["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", String(info.fps), "-movflags", "+faststart"];
    const a = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest"];
    for (const [nome, wav] of [["", "mix.wav"], ["-sem-trilha", "mix_sem_trilha.wav"]]) {
        const audio = path.join(audioDir, wav);
        const saida = `${base}${nome}.mp4`;
        if (existsSync(audio)) await run("ffmpeg", ["-y", "-loglevel", "error", "-i", mkv, "-i", audio, ...v, ...a, saida]);
        else if (!nome) await run("ffmpeg", ["-y", "-loglevel", "error", "-i", mkv, ...v, "-an", saida]);
        else continue;
        console.log(`${path.relative(RAIZ, saida)}  ${(statSync(saida).size / 1024 / 1024).toFixed(1)} MB${existsSync(audio) ? "" : " (mudo: falta a narração)"}`);
    }
    const capa = `${base}-capa.png`;
    await run("ffmpeg", ["-y", "-loglevel", "error", "-ss", String(info.capa), "-i", mkv, "-frames:v", "1", "-pix_fmt", "rgb24", capa]);
    console.log(path.relative(RAIZ, capa));
}

const [modo, ep, variante = "A", lista = ""] = process.argv.slice(2);
if (!ep || !existsSync(path.join(RAIZ, ep, "config.json"))) {
    console.log("Uso: node animacao/render.mjs <stills|video|encode|tudo> <pasta do episódio> [A|B] [t1,t2,...]");
    process.exit(1);
}
if (modo === "stills") await stills(ep, variante, lista.split(",").filter(Boolean).map(Number));
else if (modo === "video") await video(ep, variante);
else if (modo === "encode") await encode(ep, variante);
else if (modo === "tudo") await encode(ep, variante, await video(ep, variante));
else console.log("Modo desconhecido:", modo);
