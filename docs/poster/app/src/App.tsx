import type { ReactNode } from "react"
import {
  BookOpen,
  ChartLine,
  CircleCheck,
  CircleHelp,
  Cpu,
  LayoutGrid,
  Library,
  ShieldCheck,
  Telescope,
  Unplug,
  Workflow,
  type LucideIcon,
} from "lucide-react"

import { Alert, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"

import chartLatency from "./assets/chart_latency.svg"
import logo from "./assets/vesit_logo.png"

/* ---------- shared building blocks (all built on the shadcn components) ---------- */

function Section({ title, icon: Icon, grow, children }: { title: string; icon: LucideIcon; grow?: boolean; children: ReactNode }) {
  return (
    <Card className={cn("shrink-0 gap-0 rounded-xl py-0 shadow-sm ring-0 border border-border", grow && "grow")}>
      <CardHeader className="flex flex-row items-center gap-3 border-b bg-muted/60 px-5 py-2">
        <span className="flex size-[38px] items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Icon className="size-[24px]" strokeWidth={2.2} />
        </span>
        <CardTitle className="text-[30px] leading-none font-semibold tracking-tight text-primary">{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col gap-[8px] px-5 py-[11px] text-[18.5px] leading-[1.32]">
        {children}
      </CardContent>
    </Card>
  )
}

function Bullets({ children, className }: { children: ReactNode; className?: string }) {
  return <ul className={cn("list-disc space-y-[5px] pl-[22px] marker:text-primary", className)}>{children}</ul>
}

function Stat({ value, tone, children }: { value: string; tone: "good" | "bad" | "brand"; children: ReactNode }) {
  const color = { good: "text-[#0b7a3b]", bad: "text-destructive", brand: "text-primary" }[tone]
  return (
    <Card className="h-[92px] flex-row items-center gap-4 rounded-xl border border-border px-[18px] py-0 shadow-sm ring-0">
      <b className={cn("text-[46px] leading-none whitespace-nowrap", color)}>{value}</b>
      <span className="text-[18px] leading-tight text-muted-foreground">{children}</span>
    </Card>
  )
}

const Note = ({ children }: { children: ReactNode }) => (
  <p className="text-[15px] leading-[1.28] text-muted-foreground">{children}</p>
)

const th = "h-auto bg-primary px-2 py-[5px] font-bold text-primary-foreground"
const td = "px-2 py-1 text-[16.5px] leading-[1.22]"
const rowCls = "border-border even:bg-muted hover:bg-transparent"

const Holds = () => <Badge className="h-auto bg-[#e3f4ea] px-2 py-0.5 text-[16px] font-bold text-[#0b7a3b]">✓ holds</Badge>
const Fails = ({ children }: { children: ReactNode }) => (
  <Badge variant="destructive" className="h-auto bg-[#fbe6e7] px-2 py-0.5 text-[16px] font-bold">
    ✗ {children}
  </Badge>
)

const Dot = ({ c }: { c: string }) => (
  <span className="mr-1.5 inline-block size-3 rounded-full align-middle" style={{ background: c }} />
)

/* ---------- SDG badges ---------- */

function Sdgs() {
  return (
    <div className="flex gap-2">
      <svg viewBox="0 0 100 100" className="size-[104px]" fontFamily="Arial Narrow, Arial, sans-serif" aria-label="SDG 9: Industry, Innovation and Infrastructure">
        <rect width="100" height="100" fill="#FD6925" />
        <text x="6" y="27" fontSize="27" fontWeight="700" fill="#fff">9</text>
        <text fill="#fff" fontSize="8.6" fontWeight="700">
          <tspan x="24" y="12">INDUSTRY,</tspan>
          <tspan x="24" y="21">INNOVATION AND</tspan>
          <tspan x="24" y="30">INFRASTRUCTURE</tspan>
        </text>
        <g fill="none" stroke="#fff" strokeWidth="3.2" strokeLinejoin="round">
          <path d="M50 42 L72 54 L72 78 L50 90 L28 78 L28 54 Z" />
          <path d="M28 54 L50 66 L72 54 M50 66 L50 90" />
        </g>
      </svg>
      <svg viewBox="0 0 100 100" className="size-[104px]" fontFamily="Arial Narrow, Arial, sans-serif" aria-label="SDG 11: Sustainable Cities and Communities">
        <rect width="100" height="100" fill="#FD9D24" />
        <text x="5" y="27" fontSize="27" fontWeight="700" fill="#fff" letterSpacing="-1">11</text>
        <text fill="#fff" fontSize="8.6" fontWeight="700">
          <tspan x="35" y="12">SUSTAINABLE</tspan>
          <tspan x="35" y="21">CITIES AND</tspan>
          <tspan x="35" y="30">COMMUNITIES</tspan>
        </text>
        <g fill="#fff">
          <rect x="18" y="56" width="14" height="34" />
          <rect x="34" y="44" width="16" height="46" />
          <path d="M52 90 L52 66 L66 54 L80 66 L80 90 Z" />
          <rect x="82" y="70" width="6" height="20" />
        </g>
        <g fill="#FD9D24">
          <rect x="38" y="50" width="3" height="4" /><rect x="44" y="50" width="3" height="4" />
          <rect x="38" y="60" width="3" height="4" /><rect x="44" y="60" width="3" height="4" />
          <rect x="38" y="70" width="3" height="4" /><rect x="44" y="70" width="3" height="4" />
          <rect x="62" y="76" width="8" height="14" />
        </g>
      </svg>
    </div>
  )
}

/* ---------- Methodology diagram ---------- */

function Diagram() {
  return (
    <svg viewBox="0 0 600 214" className="block w-full rounded-md bg-white ring-1 ring-primary/20" fontFamily="Arial, sans-serif">
      <defs>
        <marker id="ah" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill="#382bad" />
        </marker>
      </defs>
      <rect x="10" y="8" width="104" height="32" rx="6" fill="#fff" stroke="#382bad" strokeWidth="2" />
      <text x="62" y="30" textAnchor="middle" fontSize="17" fontWeight="700">Device</text>
      <rect x="486" y="8" width="104" height="32" rx="6" fill="#fff" stroke="#382bad" strokeWidth="2" />
      <text x="538" y="30" textAnchor="middle" fontSize="17" fontWeight="700">Server</text>
      <line x1="62" y1="40" x2="62" y2="206" stroke="#b9b5e3" strokeWidth="2" />
      <line x1="538" y1="40" x2="538" y2="206" stroke="#b9b5e3" strokeWidth="2" />
      <text x="300" y="60" textAnchor="middle" fontSize="15">M1 = pseudonym PID + encrypted(nonce, period t)</text>
      <line x1="64" y1="68" x2="534" y2="68" stroke="#382bad" strokeWidth="2.5" markerEnd="url(#ah)" />
      <rect x="150" y="78" width="380" height="62" rx="6" fill="#fff3e6" stroke="#e8630a" strokeWidth="2.5" />
      <text x="340" y="99" textAnchor="middle" fontSize="16" fontWeight="700" fill="#b44a00">1. Resolution: which device sent this PID?</text>
      <text x="340" y="118" textAnchor="middle" fontSize="14">search N devices × periods for H2(secret, t) = PID</text>
      <text x="340" y="134" textAnchor="middle" fontSize="13.5" fontStyle="italic" fill="#b44a00">not specified, not in the paper's cost model</text>
      <rect x="150" y="147" width="380" height="26" rx="6" fill="#f4f3fc" stroke="#8277e6" strokeWidth="1.5" />
      <text x="340" y="165" textAnchor="middle" fontSize="14">2. decrypt with that device's key and verify (paper's cost)</text>
      <text x="300" y="190" textAnchor="middle" fontSize="15">M2 = server ID + encrypted reply → shared session key</text>
      <line x1="536" y1="198" x2="66" y2="198" stroke="#382bad" strokeWidth="2.5" markerEnd="url(#ah)" />
    </svg>
  )
}

function Step({ n, title, children }: { n: string; title: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-[46px_1fr] items-start gap-x-2">
      <div className="text-[34px] leading-none font-bold text-primary">{n}</div>
      <div>
        <h3 className="mb-px text-[19px] font-bold">{title}</h3>
        <p className="text-[16.5px] leading-[1.27]">{children}</p>
      </div>
    </div>
  )
}

/* ---------- data ---------- */

const ranked: [string, string, string, string, string, string, string, ReactNode?][] = [
  ["1", "#0072B2", "O2 counter + table", "24.25", "24.40", "24.40 ms", "92.9"],
  ["2", "#56B4E9", "O4 clock + table", "23.93", "24.22", "24.59 ms", "46.4"],
  ["3", "#555555", "MW key tree", "27.96", "30.86", "31.38 ms", "10.4"],
  ["4", "#009E73", "CR hash lock", "28.86", "51.71", "94.89 ms", "10.1"],
  ["5", "#E69F00", "O3 clock + scan", "38.99", "176.1", "1.11 s", "16.1"],
  ["6", "#CC79A7", "TM rainbow table", "516.5", "5,228", "12.9 s", "59.9"],
  ["7", "#D55E00", "O1 counter + scan", "507.9", "16,947", "44.0 s", "12.1"],
]

const refs = [
  `A. Al-Rasheed et al., "A low-cost hybrid ECC authentication protocol for trustworthy IoT communication," IEEE Trans. Consum. Electron., 72(2), 4483–4491, 2026.`,
  `S. A. Weis et al., "Security and privacy aspects of low-cost RFID systems," SPC 2003.`,
  `M. Ohkubo et al., "Cryptographic approach to 'privacy-friendly' tags," 2003.`,
  `D. Molnar and D. Wagner, "Privacy and security in library RFID," ACM CCS 2004.`,
  `G. Avoine et al., "Reducing time complexity in RFID systems," SAC 2005.`,
  `B. Blanchet, "Modeling and verifying security protocols with ProVerif," FnT Priv. Secur., 2016.`,
]

/* ---------- the poster ---------- */

export default function App() {
  return (
    <div className="flex h-[2208px] w-[1824px] flex-col gap-4 overflow-hidden bg-background px-9 pt-6 pb-[22px] font-sans text-foreground">
      <header className="flex items-center gap-6">
        <img src={logo} alt="Vivekanand Education Society's Institute of Technology" className="h-[118px] w-auto" />
        <div className="flex-1 text-center">
          <div className="text-[46px] leading-[1.18] font-semibold tracking-tight text-primary">Vivekanand Education Society’s Institute Of Technology</div>
          <div className="text-[36px] leading-[1.25] font-medium text-muted-foreground">Department Of Information Technology</div>
        </div>
        <Sdgs />
      </header>
      <Separator className="h-[4px] rounded-full bg-primary" />

      <div className="text-center">
        <h1 className="text-[58px] leading-[1.1] font-bold tracking-tight text-primary">
          Pseudonym Resolution and Formal Verification of an<br />Unlinkable Two-Message IoT Authentication Protocol
        </h1>
        <div className="mt-3 text-[32px] font-semibold">Chaitanya Kelkar, Jay Kerkar, Yash Kolekar, Chirag Poornamath</div>
        <div className="mt-1 text-[26px] font-medium text-muted-foreground">Project Guide: Dr. Shanta Sondur</div>
      </div>

      <div className="grid grid-cols-4 gap-[22px]">
        <Stat value="24.4 ms" tone="good">per session at 1,000 devices with a <strong>precomputed table</strong> (paper: 23.68 ms)</Stat>
        <Stat value="44 s" tone="bad">per session in the same network with the <strong>on-demand scan</strong></Stat>
        <Stat value="8" tone="bad">dropped messages lock a counter-based device out <strong>for good</strong></Stat>
        <Stat value="125" tone="brand">tests pass (96% coverage); session key proven secret for <strong>any</strong> correct server</Stat>
      </div>

      <div id="cols" className="grid min-h-0 flex-1 grid-cols-[540fr_636fr_540fr] gap-[22px]">
        {/* ============ column 1 ============ */}
        <div className="col flex min-h-0 flex-col gap-3 overflow-hidden">
          <Section title="Introduction" icon={BookOpen}>
            <Bullets>
              <li>Lightweight IoT protocols hide a device behind a <strong>pseudonym</strong>, a disguised ID that changes every time period, so an eavesdropper cannot link its sessions.</li>
              <li>Al-Rasheed et al. (IEEE TCE, 2026) propose one: <strong>two messages, hashing and symmetric encryption only</strong>.</li>
              <li><strong>The catch:</strong> the server can decrypt a message only once it knows who sent it, and the pseudonym hides exactly that.</li>
            </Bullets>
          </Section>

          <Section title="Problem Statement" icon={CircleHelp}>
            <Bullets>
              <li>Message M1 shows only the pseudonym; the rest is encrypted with a per-device key.</li>
              <li>So every server must first <strong>find the sender</strong> by recomputing pseudonyms from its secrets: <strong>pseudonym resolution</strong>.</li>
              <li>The specification never defines this step, and its cost model charges a <strong>fixed 23.68 ms</strong> per session for any number of devices.</li>
              <li>Two open choices set the cost: <strong>time periods</strong> (counter or clock) and <strong>search</strong> (scan on demand or precomputed table).</li>
            </Bullets>
            <Alert className="border-primary/30 bg-secondary px-4 py-2.5">
              <CircleHelp className="size-[22px] text-primary" />
              <AlertTitle className="text-[19px] font-bold text-primary">What does resolution really cost, and which choice should a deployment make?</AlertTitle>
            </Alert>
          </Section>

          <Section title="Design Space" icon={LayoutGrid}>
            <Table>
              <TableHeader>
                <TableRow className="border-0 hover:bg-transparent">
                  <TableHead className={th} />
                  <TableHead className={cn(th, "whitespace-normal")}>How the server finds the sender</TableHead>
                  <TableHead className={cn(th, "whitespace-normal")}>Probes, honest</TableHead>
                  <TableHead className={th}>Forged</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[
                  ["O1", "Counter + scan", "(N−1)W/2+L+2", "N·W"],
                  ["O2", "Counter + table", "1", "0"],
                  ["O3", "Clock + scan", <>(N−1)W<sub>t</sub>/2+1</>, <>N·W<sub>t</sub></>],
                  ["O4", "Clock + table", "0 (+N/period)", "0"],
                  ["TM", "Rainbow time-memory table", <>≈0.5–0.7 S<sup>2/3</sup></>, <>≈4 S<sup>2/3</sup></>],
                  ["CR", "Randomised hash lock *", "(N+1)/2", "N"],
                  ["MW", "Key tree *", "≤ δ·d", "≤ δ"],
                ].map(([k, a, b, c]) => (
                  <TableRow key={String(k)} className={rowCls}>
                    <TableCell className={cn(td, "font-bold")}>{k}</TableCell>
                    <TableCell className={td}>{a}</TableCell>
                    <TableCell className={td}>{b}</TableCell>
                    <TableCell className={td}>{c}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <Note>Probe = one hash (0.32 ms). N devices; W = 25 periods (L = 16 back, F = 8 ahead); W<sub>t</sub> = 3; S = 128N; δ = 32. * Adds a random value to M1.</Note>
          </Section>

          <Section title="Desynchronisation" icon={Unplug}>
            <Bullets>
              <li>A counter device advances on every attempt; the server looks only <strong>8 periods ahead</strong>.</li>
              <li>Dropping <strong>8 messages in a row locks the device out for good</strong> (7 drops: it recovers). Tested for O1 and O2.</li>
              <li>Clock periods, CR and MW cannot fall out of sync.</li>
            </Bullets>
          </Section>

          <Section title="Future Scope" icon={Telescope} grow>
            <Bullets>
              <li>Stateful proof of replay protection (e.g. Tamarin).</li>
              <li>Hardware timings on the ESP8266; full CR and MW messages.</li>
            </Bullets>
          </Section>
        </div>

        {/* ============ column 2 ============ */}
        <div className="col flex min-h-0 flex-col gap-3 overflow-hidden">
          <Section title="Methodology" icon={Workflow}>
            <Diagram />
            <div className="grid grid-cols-2 gap-x-4 gap-y-2">
              <Step n="01" title="Reproduce">Python and ESP8266 C versions of the exchange match independent test vectors byte for byte.</Step>
              <Step n="02" title="Count">Seven strategies, 1 to 10,000 devices; every hash counted and checked against formulas.</Step>
              <Step n="03" title="Simulate">OMNeT++ 6.4 model of the paper's network; 5% adversaries forging 1 msg/s; 960 runs.</Step>
              <Step n="04" title="Prove">ProVerif 2.05 models of secrecy, authentication and unlinkability.</Step>
            </div>
          </Section>

          <Section title="Results" icon={ChartLine} grow>
            <div className="rounded-md bg-white p-1 ring-1 ring-primary/20">
              <img src={chartLatency} alt="Mean session time against network size" className="block w-full" />
            </div>
            <Note>Mean session time (log scale), OMNeT++ model of the paper's network (1500×1500 m, 10 Mbps, servers = 5% of devices), five seeds.</Note>
            <Table>
              <TableHeader>
                <TableRow className="border-0 hover:bg-transparent">
                  <TableHead className={th}>#</TableHead>
                  <TableHead className={th}>Strategy</TableHead>
                  <TableHead className={cn(th, "text-right")}>100</TableHead>
                  <TableHead className={cn(th, "text-right")}>500</TableHead>
                  <TableHead className={cn(th, "text-right")}>1,000 devices</TableHead>
                  <TableHead className={cn(th, "text-right")}>KB/server</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ranked.map(([n, c, name, a, b, d, kb]) => (
                  <TableRow key={n} className={rowCls}>
                    <TableCell className={cn(td, "font-bold")}>{n}</TableCell>
                    <TableCell className={td}><Dot c={c} />{name}</TableCell>
                    <TableCell className={cn(td, "text-right")}>{a}</TableCell>
                    <TableCell className={cn(td, "text-right")}>{b}</TableCell>
                    <TableCell className={cn(td, "text-right", (n === "1" || n === "2") && "font-bold", n === "7" && "font-bold text-destructive")}>{d}</TableCell>
                    <TableCell className={cn(td, "text-right")}>{kb}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <Note>Mean session time in ms, ranked at 1,000 devices; all strategies give the paper's 23.68 ms at one device.</Note>
            <Bullets>
              <li><strong>Tables (O2, O4) stay within 1 ms of the paper</strong> up to 1,000 devices, for 93 KB and 46 KB per server.</li>
              <li><strong>The counter scan (O1) reaches 44 s</strong>: honest load alone gives 19.2 s, and each forged pseudonym forces a full scan the block-list never sees.</li>
              <li><strong>A forged message costs O1 25,000 hashes</strong> at 1,000 devices, but O2 and O4 nothing: a table miss needs no hash.</li>
            </Bullets>
          </Section>
        </div>

        {/* ============ column 3 ============ */}
        <div className="col flex min-h-0 flex-col gap-3 overflow-hidden">
          <Section title="Formal Verification" icon={ShieldCheck}>
            <p>ProVerif 2.05, active attacker. The server may match a pseudonym to <strong>any</strong> enrolled device, so results hold for every correct resolver.</p>
            <Table>
              <TableHeader>
                <TableRow className="border-0 hover:bg-transparent">
                  <TableHead className={th}>Property</TableHead>
                  <TableHead className={th}>Result</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[
                  ["Q1/Q2", "Session key stays secret", <Holds />],
                  ["Q3", "Server knows who it talked to", <Holds />],
                  ["Q4", "… and never accepts M1 twice", <Fails>replay</Fails>],
                  ["Q5", "Device and server agree on the key", <Holds />],
                  ["FS", "Old keys safe after a key leak", <Fails>not claimed</Fails>],
                  ["U1", "Unlinkable, counter periods", <Holds />],
                  ["U2", "Unlinkable, clock periods", <Fails>same PID</Fails>],
                ].map(([k, label, res]) => (
                  <TableRow key={String(k)} className={rowCls}>
                    <TableCell className={td}><b>{k}</b> {label}</TableCell>
                    <TableCell className={td}>{res}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <p>Q4 needs the replay state the specification leaves open; with clock periods, two sessions in one period share a PID and can be linked.</p>
          </Section>

          <Section title="Implementation" icon={Cpu}>
            <Bullets>
              <li><strong>Python package</strong> (crypto, trusted authority, device, server, five resolvers, TCP demo) and an <strong>ESP8266 C port</strong>: 5 of 5 handshakes agree.</li>
              <li><strong>125 tests pass</strong>, 96% coverage: unit, property (10,000 trials) and adversarial.</li>
            </Bullets>
            <pre className="rounded-md bg-[#1f2430] px-3 py-[9px] font-mono text-[14.5px] leading-[1.42] whitespace-pre text-[#d8dee9]">
              <span className="text-[#8fbcbb]">$ hea-device authenticate ...</span>{"\n"}
              <span className="text-[#a3be8c]">Mutual authentication succeeded with 'server-A'.</span>{"\n"}
              {"  round-trip latency: 2.103 ms\n"}
              <span className="text-[#8fbcbb]">$ hea-device authenticate ... --replay-last</span>{"\n"}
              <span className="text-[#ef6b73]">REJECTED by server: ReplayDetected (stale epoch 0)</span>
            </pre>
          </Section>

          <Section title="Conclusion" icon={CircleCheck}>
            <Bullets>
              <li><strong>Counter periods:</strong> precompute a table (O2), one probe per login, and add a resync path.</li>
              <li><strong>Clocks:</strong> O4 uses half the memory, but same-period sessions are linkable.</li>
              <li><strong>Scan on demand</strong> (O1, O3) only in small, trusted networks.</li>
              <li><strong>The specification</strong> should state these choices and cost resolution.</li>
            </Bullets>
          </Section>

          <Section title="References" icon={Library} grow>
            <ol className="list-decimal space-y-[3px] pl-[22px] text-[15px] leading-[1.26] marker:text-primary">
              {refs.map((r) => <li key={r}>{r}</li>)}
            </ol>
            <Note><strong>Code and data:</strong> github.com/jaykerkar0405/hybrid-ecc-iot-auth</Note>
          </Section>
        </div>
      </div>

      <Card className="h-[58px] shrink-0 items-center justify-center rounded-xl bg-primary py-0 text-[25px] font-bold whitespace-nowrap text-primary-foreground ring-0">
        <span>Find the sender first:&nbsp;<em className="text-[#ffd27a] not-italic">a precomputed table keeps 24.4 ms at 1,000 devices; an on-demand scan takes 44 s.</em></span>
      </Card>
    </div>
  )
}
