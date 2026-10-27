// Builds hybrid-ecc-audit.pptx. Run from a directory where pptxgenjs, react,
// react-dom, react-icons and sharp resolve (set NODE_PATH if needed):
//   node build_deck.js
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const RDS = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require(path.join(
  process.env.PPTX_SKILL_DIR || "/Users/anonjr/.claude/skills/synced/13d9497b-efb1-4010-a72a-0bff6a341ed6_99f077b6-7649-4434-92bd-6ac5d0046261/pptx",
  "scripts/apply_theme.js"
));

const OUT = process.env.DECK_OUT || path.join(__dirname, "hybrid-ecc-audit.pptx");

const THEME = {
  name: "Research Audit",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B1F2A", lt1: "FFFFFF", dk2: "1F3A5F", lt2: "F1F4F8",
    accent1: "1F3A5F", accent2: "C0452F", accent3: "2A7F62",
    accent4: "6B7486", accent5: "D9A441", accent6: "5B7DB1",
    hlink: "1F3A5F", folHlink: "6B7486",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Do the Numbers Hold on Real Hardware?";
pres.author = "Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar";
const C = pres.SchemeColor;

async function icon(Comp, color) {
  const svg = RDS.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: "256" }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.4, w: 9, h: 0.75, fontSize: 30, bold: true, color: C.text2, margin: 0, align: "left", valign: "top" }, text: "" } },
    { text: { text: "Reproducibility audit of a hybrid ECC authentication protocol for IoT", options: { x: 0.5, y: 5.2, w: 6.5, h: 0.25, fontSize: 10, color: C.accent4, margin: 0, isTextBox: true } } },
  ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.25, fontSize: 10, color: C.accent4, align: "right" },
});
pres.defineSlideMaster({
  title: "DARK",
  background: { color: HEX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.7, y: 1.2, w: 8.6, h: 1.7, fontSize: 38, bold: true, color: C.background1, margin: 0, align: "left", valign: "top" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.7, y: 3.05, w: 8.0, h: 0.9, fontSize: 18, color: C.background2, margin: 0, valign: "top" }, text: "" } },
  ],
});

pres.defineSlideMaster({
  title: "CLOSE",
  background: { color: HEX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.7, y: 1.0, w: 8.6, h: 0.9, fontSize: 38, bold: true, color: C.background1, margin: 0, align: "left", valign: "top" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.7, y: 2.1, w: 8.2, h: 2.0, fontSize: 20, color: C.background2, margin: 0, align: "left", valign: "top" }, text: "" } },
  ],
});

// ---------- helpers ----------
const card = (s, name, x, y, w, h, extra = {}) =>
  s.addShape(pres.ShapeType.roundRect, { objectName: name, x, y, w, h, rectRadius: 0.08, fill: { color: C.background2 }, line: { type: "none" }, ...extra });

const txt = (s, name, text, o) => s.addText(text, { objectName: name, isTextBox: true, margin: 0, ...o });

async function iconCircle(s, name, Comp, x, y, d, fillColor = C.text2, iconColor = HEX.lt1) {
  s.addShape(pres.ShapeType.ellipse, { objectName: name + " circle", x, y, w: d, h: d, fill: { color: fillColor }, line: { type: "none" } });
  const p = d * 0.5;
  s.addImage({ data: await icon(Comp, iconColor), x: x + (d - p) / 2, y: y + (d - p) / 2, w: p, h: p, altText: name });
}

const chartBase = {
  catAxisLabelColor: HEX.accent4, valAxisLabelColor: HEX.accent4,
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 12, valAxisLabelFontSize: 11, dataLabelFontSize: 14, dataLabelColor: HEX.dk1,
  valGridLine: { color: "E1E5EC", size: 0.75 }, catGridLine: { style: "none" },
  showLegend: false, showTitle: true, titleFontFace: "+mn-lt", titleFontSize: 13, titleColor: HEX.accent4,
};

(async () => {
  pres.addSection({ title: "Context" });
  // 1 ------------------------------------------------------------------ title
  let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Context" });
  s.addText("Do the Numbers Hold on Real Hardware?", { placeholder: "title" });
  s.addText("A reproducibility and measurement audit of a low-cost hybrid ECC authentication protocol for IoT", { placeholder: "body" });
  txt(s, "Authors", [
    { text: "Jay Kerkar · Chaitanya Kelkar · Chirag Poornamath · Yash Kolekar", options: { breakLine: true, bold: true } },
    { text: "Project guide: Dr. Shanta Sondur", options: {} },
  ], { x: 0.7, y: 4.35, w: 8.6, h: 0.7, fontSize: 14, color: C.background2, valign: "top" });
  s.addNotes("We audited a 2026 IEEE TCE paper on lightweight IoT authentication: we implemented its protocol, ran it on a real microcontroller, and re-checked its cost claims with measured numbers.");

  // 2 ------------------------------------------------------------- the claim
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Context" });
  s.addText("Tiny devices need cheap authentication", { placeholder: "title" });
  const rows = [
    [fa.FaMicrochip, "The device is weak", "Little memory and a slow processor, so heavy cryptography is costly."],
    [fa.FaHandshake, "It must prove who it is", "Device and server authenticate each other before any data is exchanged."],
    [fa.FaFileAlt, "The base paper claims savings", "Al-Rasheed et al., IEEE TCE 72(2), May 2026, proposes a lighter protocol."],
  ];
  for (let i = 0; i < rows.length; i++) {
    const y = 1.5 + i * 1.15;
    await iconCircle(s, "Icon " + rows[i][1], rows[i][0], 0.5, y, 0.7);
    txt(s, "Row head " + (i + 1), rows[i][1], { x: 1.45, y, w: 4.3, h: 0.35, fontSize: 18, bold: true, color: C.text2, valign: "top" });
    txt(s, "Row text " + (i + 1), rows[i][2], { x: 1.45, y: y + 0.38, w: 4.3, h: 0.65, fontSize: 14, color: C.text1, valign: "top" });
  }
  card(s, "Claim panel", 6.1, 1.4, 3.4, 3.55);
  txt(s, "Claim panel head", "Claimed reduction vs. prior schemes", { x: 6.35, y: 1.55, w: 2.9, h: 0.5, fontSize: 13, color: C.accent4, valign: "top" });
  const claims = [["17%", "communication"], ["21%", "processing"], ["12%", "storage"]];
  claims.forEach(([n, l], i) => {
    const y = 2.1 + i * 0.95;
    txt(s, "Claim number " + l, n, { x: 6.35, y, w: 1.4, h: 0.8, fontSize: 40, bold: true, color: C.text2, fontFace: "Cambria", valign: "middle" });
    txt(s, "Claim label " + l, l, { x: 7.8, y, w: 1.55, h: 0.8, fontSize: 16, color: C.text1, valign: "middle" });
  });
  s.addNotes("The base paper says its protocol is about 17% cheaper in communication, 21% in processing and 12% in storage than earlier schemes. Our question: do those numbers hold on real hardware?");

  // 3 --------------------------------------------------------- the protocol
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Context" });
  s.addText("The protocol: two messages, one shared key", { placeholder: "title" });
  card(s, "Device box", 0.5, 1.5, 2.2, 1.9, { fill: { color: C.text2 } });
  txt(s, "Device label", [
    { text: "IoT device", options: { bold: true, fontSize: 18, breakLine: true } },
    { text: "holds secret λ", options: { fontSize: 14 } },
  ], { x: 0.5, y: 1.5, w: 2.2, h: 1.9, color: C.background1, align: "center", valign: "middle" });
  card(s, "Server box", 7.3, 1.5, 2.2, 1.9, { fill: { color: C.text2 } });
  txt(s, "Server label", [
    { text: "Server", options: { bold: true, fontSize: 18, breakLine: true } },
    { text: "holds secret λ", options: { fontSize: 14 } },
  ], { x: 7.3, y: 1.5, w: 2.2, h: 1.9, color: C.background1, align: "center", valign: "middle" });
  s.addShape(pres.ShapeType.line, { objectName: "M1 arrow", x: 2.85, y: 2.15, w: 4.3, h: 0, line: { color: HEX.accent2, width: 2.5, endArrowType: "triangle" } });
  txt(s, "M1 label", [
    { text: "M1  ", options: { bold: true, color: C.accent2 } },
    { text: "fresh pseudonym, encrypted nonce Ni, tag", options: {} },
  ], { x: 2.85, y: 1.6, w: 4.3, h: 0.45, fontSize: 13, color: C.text1, align: "center", valign: "bottom" });
  s.addShape(pres.ShapeType.line, { objectName: "M2 arrow", x: 2.85, y: 3.05, w: 4.3, h: 0, flipH: true, line: { color: HEX.accent3, width: 2.5, endArrowType: "triangle" } });
  txt(s, "M2 label", [
    { text: "M2  ", options: { bold: true, color: C.accent3 } },
    { text: "server nonce Nj, proof it knew the secret", options: {} },
  ], { x: 2.85, y: 2.5, w: 4.3, h: 0.45, fontSize: 13, color: C.text1, align: "center", valign: "bottom" });
  card(s, "Session key card", 0.5, 3.7, 5.5, 1.25);
  txt(s, "Session key head", "Both sides then compute the same session key", { x: 0.75, y: 3.82, w: 5.0, h: 0.3, fontSize: 14, color: C.accent4, valign: "top" });
  txt(s, "Session key formula", "K = KDF( k* ‖ Ni ‖ Nj ‖ t )", { x: 0.75, y: 4.2, w: 5.0, h: 0.55, fontSize: 22, bold: true, fontFace: "Courier New", color: C.text2, valign: "middle" });
  card(s, "Offline online card", 6.3, 3.7, 3.2, 1.25);
  txt(s, "Offline online text", [
    { text: "Where is the ECC?", options: { bold: true, color: C.text2, breakLine: true } },
    { text: "Only offline, when a trusted authority issues secrets. Online: hashes, AES-GCM, HKDF.", options: {} },
  ], { x: 6.5, y: 3.8, w: 2.8, h: 1.05, fontSize: 13, color: C.text1, valign: "top" });
  s.addNotes("The paper's Section III protocol. The device sends a one-time pseudonym with an encrypted nonce; the server answers with its nonce and a proof; both derive the session key. The elliptic-curve part is only used during offline registration, hence 'hybrid'.");

  // 4 --------------------------------------------------- how cost was claimed
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Context" });
  s.addText("How the paper argued it is cheap", { placeholder: "title" });
  card(s, "Formula card", 0.5, 1.4, 9, 0.85);
  txt(s, "Formula", "cost  =  n_hash × T_H  +  n_enc × T_SE/D  +  n_ECC × T_ECM", { x: 0.75, y: 1.4, w: 8.5, h: 0.85, fontSize: 15, bold: true, fontFace: "Courier New", color: C.text2, valign: "middle" });
  const prices = [["T_H", "0.32 ms", "one SHA-1 hash"], ["T_SE/D", "5.6 ms", "one symmetric encrypt / decrypt"], ["T_ECM", "17.1 ms", "one ECC scalar multiplication"]];
  prices.forEach(([k, v, d], i) => {
    const x = 0.5 + i * 3.1;
    card(s, "Price card " + k, x, 2.5, 2.8, 1.35, { fill: { color: C.background1 }, line: { color: "D5DBE5", width: 1 } });
    txt(s, "Price name " + k, k + "  (assumed)", { x: x + 0.2, y: 2.6, w: 2.4, h: 0.3, fontSize: 12, color: C.accent4, fontFace: "Courier New", valign: "top" });
    txt(s, "Price value " + k, v, { x: x + 0.2, y: 2.9, w: 2.4, h: 0.55, fontSize: 30, bold: true, fontFace: "Cambria", color: C.text2, valign: "middle" });
    txt(s, "Price desc " + k, d, { x: x + 0.2, y: 3.45, w: 2.4, h: 0.3, fontSize: 12, color: C.text1, valign: "top" });
  });
  card(s, "Warning card", 0.5, 4.1, 9, 0.85, { fill: { color: C.accent2, transparency: 88 } });
  await iconCircle(s, "Warning icon", fa.FaExclamationTriangle, 0.7, 4.22, 0.6, C.accent2);
  txt(s, "Warning text", "These prices were assumed, not measured. The OMNeT++ simulation behind Fig. 1 has no published code, scenario or data, so it cannot be re-run.", { x: 1.5, y: 4.1, w: 7.8, h: 0.85, fontSize: 14, color: C.text1, valign: "middle" });
  s.addNotes("The paper counts operations and multiplies by assumed per-operation times, plus an OMNeT++ simulation that nobody can re-run. That is why there is no 'dataset': a protocol-cost paper's reproducible inputs are the specification, the constants and the operation counts, and we used all three.");

  // 5 ------------------------------------------------------------- what we did
  pres.addSection({ title: "Audit" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Audit" });
  s.addText("What we did", { placeholder: "title" });
  const steps = [
    [fa.FaSearch, "1  Audit", "Checked every table and figure against the paper's own text."],
    [fa.FaCode, "2  Implement", "Python reference plus an independent C core, equation by equation."],
    [fa.FaStopwatch, "3  Measure", "ESP8266 at 80 and 160 MHz, cloud Graviton2, laptop. Median of 100 runs."],
    [fa.FaCalculator, "4  Recompute", "Re-ran the paper's own cost model with measured prices."],
  ];
  for (let i = 0; i < steps.length; i++) {
    const x = 0.5 + i * 2.3;
    card(s, "Step card " + (i + 1), x, 1.45, 2.1, 2.55);
    await iconCircle(s, "Step icon " + (i + 1), steps[i][0], x + 0.2, 1.65, 0.6);
    txt(s, "Step head " + (i + 1), steps[i][1], { x: x + 0.2, y: 2.42, w: 1.7, h: 0.35, fontSize: 18, bold: true, color: C.text2, valign: "top" });
    txt(s, "Step text " + (i + 1), steps[i][2], { x: x + 0.2, y: 2.82, w: 1.7, h: 1.1, fontSize: 13, color: C.text1, valign: "top" });
  }
  card(s, "Evidence strip", 0.5, 4.2, 9, 0.75, { fill: { color: C.accent3, transparency: 88 } });
  txt(s, "Evidence text", [
    { text: "108 tests pass.  ", options: { bold: true } },
    { text: "The C device on the ESP8266 and the Python server complete 20 of 20 handshakes with identical session keys; replays are rejected.", options: {} },
  ], { x: 0.75, y: 4.2, w: 8.5, h: 0.75, fontSize: 14, color: C.text1, valign: "middle" });
  s.addNotes("We implement Section III of the base paper (the nonce-based protocol), not the replayable Section II variant. Same C source on every platform so the comparison is fair.");

  // 6 ------------------------------------------------- numbers do not derive
  pres.addSection({ title: "Findings" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
  s.addText("Finding 1: numbers don't reproduce", { placeholder: "title" });
  card(s, "Stat panel", 0.5, 1.45, 3.3, 3.5);
  txt(s, "Stat number", "0 of 9", { x: 0.7, y: 1.75, w: 2.9, h: 0.95, fontSize: 48, bold: true, fontFace: "Cambria", color: C.accent2, valign: "middle" });
  txt(s, "Stat text", "ways of computing 17 / 21 / 12 % from the paper's own tables give those values.", { x: 0.7, y: 2.8, w: 2.9, h: 1.6, fontSize: 16, color: C.text1, valign: "top" });
  const th = (t) => ({ text: t, options: { bold: true, color: HEX.lt1, fill: { color: HEX.dk2 }, fontSize: 13 } });
  const td = (t, o = {}) => ({ text: t, options: { fontSize: 14, color: HEX.dk1, ...o } });
  s.addTable([
    [th("What is reported"), th("Table IV"), th("Text")],
    [td("Messages"), td("4", { bold: true, color: HEX.accent2 }), td("2", { bold: true, color: HEX.accent2 })],
    [td("Bits"), td("1,024", { bold: true, color: HEX.accent2 }), td("264", { bold: true, color: HEX.accent2 })],
  ], { objectName: "Contradiction table", x: 4.1, y: 1.45, w: 5.4, colW: [2.4, 1.5, 1.5], rowH: 0.45, border: { type: "solid", pt: 0.75, color: "D5DBE5" }, valign: "middle" });
  txt(s, "Finding bullets", [
    { text: "Fig. 1 is captioned “processing”, but its axis shows communication overhead.", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } },
    { text: "One competitor row has its device and server counts swapped.", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } },
    { text: "The simulation cannot be re-run, so Fig. 1 cannot be checked.", options: { bullet: true } },
  ], { x: 4.1, y: 3.25, w: 5.4, h: 1.7, fontSize: 14, color: C.text1, valign: "top" });
  s.addNotes("We do not say the authors' simulation is wrong. We say the headline percentages cannot be derived from what was published, and the paper's table contradicts its own text.");

  // 7 -------------------------------------------------- constants are wrong
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
  s.addText("Finding 2: the assumed prices are wrong", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [{ name: "ECC cost in hash units", labels: ["Paper's assumption", "Measured on ESP8266"], values: [53, 7604] }], {
    ...chartBase, objectName: "ECC ratio chart", x: 0.5, y: 1.4, w: 4.2, h: 3.55, barDir: "col", barGapWidthPct: 60,
    chartColors: [HEX.accent4, HEX.accent2], title: "ECC op cost, in SHA-1 hashes",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "#,##0", valAxisLabelFormatCode: "#,##0", valAxisMaxVal: 9000, valAxisMajorUnit: 3000,
  });
  s.addTable([
    [th("Operation"), th("Assumed"), th("Measured"), th("Off by")],
    [td("ECC P-256"), td("17.1 ms"), td("276 ms"), td("16× slower", { bold: true, color: HEX.accent2 })],
    [td("SHA-1"), td("0.32 ms"), td("0.036 ms"), td("8.8× faster", { bold: true, color: HEX.accent3 })],
    [td("AES-GCM"), td("5.6 ms"), td("0.5–1.2 ms"), td("5–12× faster", { bold: true, color: HEX.accent3 })],
  ], { objectName: "Constants table", x: 5.0, y: 1.45, w: 4.5, colW: [1.05, 1.0, 1.15, 1.3], rowH: 0.48, border: { type: "solid", pt: 0.75, color: "D5DBE5" }, valign: "middle" });
  txt(s, "Constants note", "Same C source on every platform; ratios are identical at 80 and 160 MHz and on a second board. Medians of 100 runs.", { x: 5.0, y: 3.55, w: 4.5, h: 0.8, fontSize: 12, color: C.accent4, valign: "top" });
  txt(s, "Constants takeaway", "ECC is far costlier, and symmetric crypto far cheaper, than the paper's cost model assumes.", { x: 5.0, y: 4.25, w: 4.5, h: 0.7, fontSize: 14, bold: true, color: C.text2, valign: "top" });
  s.addNotes("On the ESP8266 a P-256 scalar multiplication takes 276 ms, 16 times the paper's constant, while hashing and AES-GCM are 5 to 12 times cheaper than assumed. The ratio of ECC to hash is 7,604 against an assumed 53.");

  // 8 -------------------------------------------------------- ranking
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
  s.addText("Finding 3: the ranking cuts both ways", { placeholder: "title" });
  card(s, "Good panel", 0.5, 1.45, 4.35, 2.45);
  txt(s, "Good head", "Versus ECC-based schemes", { x: 0.75, y: 1.6, w: 3.9, h: 0.35, fontSize: 15, color: C.accent4, valign: "top" });
  txt(s, "Good number", "60–2,520×", { x: 0.75, y: 2.0, w: 3.9, h: 0.9, fontSize: 40, bold: true, fontFace: "Cambria", color: C.accent3, valign: "middle" });
  txt(s, "Good text", "cheaper than the paper claims. The scheme wins, by far more than reported.", { x: 0.75, y: 2.95, w: 3.9, h: 0.8, fontSize: 14, color: C.text1, valign: "top" });
  card(s, "Bad panel", 5.15, 1.45, 4.35, 2.45);
  txt(s, "Bad head", "Versus hash-only schemes", { x: 5.4, y: 1.6, w: 3.9, h: 0.35, fontSize: 15, color: C.accent4, valign: "top" });
  txt(s, "Bad number", "3.8–13.7×", { x: 5.4, y: 2.0, w: 3.9, h: 0.9, fontSize: 40, bold: true, fontFace: "Cambria", color: C.accent2, valign: "middle" });
  txt(s, "Bad text", "more expensive, once the session-key derivation is counted. The paper says the opposite.", { x: 5.4, y: 2.95, w: 3.9, h: 0.8, fontSize: 14, color: C.text1, valign: "top" });
  txt(s, "Ranking why", [
    { text: "Why: ", options: { bold: true, color: C.text2 } },
    { text: "the paper's own Eq. 16 needs a key-derivation step (HKDF, 629 µs, about 17 hashes) that its cost table leaves out.", options: {} },
  ], { x: 0.5, y: 4.15, w: 9, h: 0.8, fontSize: 15, color: C.text1, valign: "top" });
  s.addNotes("The ranking flips back only if the symmetric step is read as unauthenticated AES, which would drop the MAC the protocol requires. We report four readings of the cost and say which one we think is right.");

  // 9 ------------------------------------------------- forward secrecy
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
  s.addText("Finding 4: no forward secrecy", { placeholder: "title" });
  const fs = [
    [fa.FaVideo, "1  Record", "An attacker saves encrypted sessions today."],
    [fa.FaKey, "2  Steal", "Later, the long-term secret k* leaks."],
    [fa.FaLockOpen, "3  Decrypt", "Every past session key is rebuilt: 5 of 5 in our test."],
  ];
  for (let i = 0; i < fs.length; i++) {
    const x = 0.5 + i * 3.2;
    card(s, "FS card " + (i + 1), x, 1.5, 2.7, 2.1, i === 2 ? { fill: { color: C.accent2, transparency: 88 } } : {});
    await iconCircle(s, "FS icon " + (i + 1), fs[i][0], x + 0.25, 1.7, 0.6, i === 2 ? C.accent2 : C.text2);
    txt(s, "FS head " + (i + 1), fs[i][1], { x: x + 0.25, y: 2.4, w: 2.3, h: 0.35, fontSize: 18, bold: true, color: C.text2, valign: "top" });
    txt(s, "FS text " + (i + 1), fs[i][2], { x: x + 0.25, y: 2.8, w: 2.3, h: 0.7, fontSize: 14, color: C.text1, valign: "top" });
    if (i < 2) s.addShape(pres.ShapeType.line, { objectName: "FS arrow " + (i + 1), x: x + 2.78, y: 2.55, w: 0.34, h: 0, line: { color: HEX.accent4, width: 2, endArrowType: "triangle" } });
  }
  txt(s, "FS explain", [
    { text: "Why: ", options: { bold: true, color: C.text2 } },
    { text: "K = KDF(k* ‖ Ni ‖ Nj ‖ t) uses no ephemeral secret, so k* plus recorded traffic rebuilds K. Fixing it needs a fresh key exchange per session, which is an ECC operation (276 ms on our chip).", options: {} },
  ], { x: 0.5, y: 3.85, w: 9, h: 1.1, fontSize: 14, color: C.text1, valign: "top" });
  s.addNotes("This is an attack script, not a formal proof. It shows the design property: compromise of the long-term secret exposes all past sessions.");

  // 10 ------------------------------------------------- server loop
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
  s.addText("Finding 5: the server does a hidden loop", { placeholder: "title" });
  card(s, "Code card", 0.5, 1.45, 4.6, 1.85, { fill: { color: C.text2 } });
  txt(s, "Lookup code", "for device in all_devices:\n    for t in epoch_window:\n        if H2(device.secret, t) == pid:\n            return device", { x: 0.7, y: 1.55, w: 4.3, h: 1.65, fontSize: 12, fontFace: "Courier New", color: C.background1, align: "left", valign: "middle" });
  txt(s, "Loop text", "Pseudonyms change every message, so the server cannot look one up. It tries every device, and the cost grows with the fleet. The paper's table treats server cost as a constant.", { x: 0.5, y: 3.5, w: 4.6, h: 1.45, fontSize: 14, color: C.text1, valign: "top" });
  s.addChart(pres.charts.BAR, [{ name: "Lookup time (ms)", labels: ["1,000 devices", "5,000 devices"], values: [4.8, 23.9] }], {
    ...chartBase, objectName: "Lookup chart", x: 5.4, y: 1.4, w: 4.1, h: 3.1, barDir: "col", barGapWidthPct: 70,
    chartColors: [HEX.accent6, HEX.accent2], title: "Server lookup per request (ms)",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", valAxisLabelFormatCode: "0", valAxisMaxVal: 30, valAxisMajorUnit: 10,
  });
  txt(s, "Lookup note", "A precomputed table removes the loop at the price of memory (about 416 KB in our setup).", { x: 5.4, y: 4.55, w: 4.1, h: 0.45, fontSize: 12, color: C.accent4, valign: "top" });
  s.addNotes("Measured with a 13-epoch window. This is a scaling cost the paper's operation-count table cannot show.");

  // 11 ------------------------------------------------- real chip
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
  s.addText("It does run on a real microcontroller", { placeholder: "title" });
  const stats = [
    ["5.26 ms", "device compute per handshake", "1.67 build + 3.59 verify"],
    ["216 B", "first message (M1)", "52 ms over Wi-Fi"],
    ["276 ms", "one ECC multiplication", "on the same chip"],
    ["≈ 52×", "that ECC op vs. the whole handshake", "276 ms ÷ 5.26 ms"],
  ];
  stats.forEach(([n, l, sub], i) => {
    const x = 0.5 + i * 2.3;
    card(s, "Stat tile " + (i + 1), x, 1.5, 2.1, 2.5);
    txt(s, "Tile number " + (i + 1), n, { x: x + 0.15, y: 1.65, w: 1.8, h: 0.8, fontSize: 28, bold: true, fontFace: "Cambria", color: i === 3 ? C.accent2 : C.text2, valign: "middle" });
    txt(s, "Tile label " + (i + 1), l, { x: x + 0.15, y: 2.5, w: 1.8, h: 0.8, fontSize: 14, color: C.text1, valign: "top" });
    txt(s, "Tile sub " + (i + 1), sub, { x: x + 0.15, y: 3.4, w: 1.8, h: 0.45, fontSize: 12, color: C.accent4, valign: "top" });
  });
  txt(s, "Chip takeaway", "The protocol itself is genuinely light. The paper's weakness is its evidence and its constants, not the idea.", { x: 0.5, y: 4.25, w: 9, h: 0.7, fontSize: 16, bold: true, color: C.text2, valign: "top" });
  s.addNotes("This is an ESP8266 at 80 MHz. We are fair to the protocol: it is cheap online. Our critique is about the evidence behind the headline percentages.");

  // 12 ------------------------------------------------- limits
  pres.addSection({ title: "Wrap-up" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Wrap-up" });
  s.addText("What we show, and what we don't claim", { placeholder: "title" });
  card(s, "Show panel", 0.5, 1.4, 4.35, 3.55);
  txt(s, "Show head", "We show", { x: 0.75, y: 1.55, w: 3.9, h: 0.35, fontSize: 18, bold: true, color: C.accent3, valign: "top" });
  txt(s, "Show list", [
    { text: "Headline savings are not derivable from the published tables", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } },
    { text: "Cost constants are off by 16× and 5–12×", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } },
    { text: "The ranking depends on counting the KDF", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } },
    { text: "No forward secrecy; server cost grows with devices", options: { bullet: true } },
  ], { x: 0.75, y: 2.0, w: 3.9, h: 2.8, fontSize: 14, color: C.text1, valign: "top" });
  card(s, "Dont panel", 5.15, 1.4, 4.35, 3.55);
  txt(s, "Dont head", "We do not claim", { x: 5.4, y: 1.55, w: 3.9, h: 0.35, fontSize: 18, bold: true, color: C.accent2, valign: "top" });
  txt(s, "Dont list", [
    { text: "That the authors' simulation is wrong, only that it cannot be reproduced", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } },
    { text: "Results beyond one ESP8266 and one crypto library", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } },
    { text: "That we re-implemented the rivals; two table rows were matched via secondary sources only", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } },
    { text: "A formal security proof; the authors were not contacted", options: { bullet: true } },
  ], { x: 5.4, y: 2.0, w: 3.9, h: 2.8, fontSize: 14, color: C.text1, valign: "top" });
  s.addNotes("Be upfront about the limits: single MCU, single library, competitors not re-implemented, no formal analysis, authors not contacted.");

  // 13 ------------------------------------------------- takeaway
  s = pres.addSlide({ masterName: "CLOSE", sectionTitle: "Wrap-up" });
  s.addText("Take-away", { placeholder: "title" });
  s.addText("The savings cannot be reproduced from what was published. On real hardware the scheme beats ECC-heavy rivals by a wide margin, loses to hash-only ones, has no forward secrecy, and its server cost grows with the fleet.", { placeholder: "body" });
  txt(s, "Reference", "Base paper: Al-Rasheed et al., IEEE Trans. Consumer Electronics 72(2), 4483–4491, May 2026. DOI 10.1109/TCE.2026.3662053", { x: 0.7, y: 4.55, w: 8.6, h: 0.5, fontSize: 12, color: C.background2, valign: "top" });
  s.addNotes("One sentence: the numbers do not hold as published; the protocol is still cheap, but not in the way, or by the margin, the paper says.");

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
