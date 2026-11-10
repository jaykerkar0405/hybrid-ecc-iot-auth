import { StrictMode } from "react"
import { createRoot } from "react-dom/client"

import App from "./App.tsx"
import "./index.css"

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
)

// Layout check read by poster/build.py: how many px each column's content exceeds its box (must be <= 0).
addEventListener("load", () => {
  setTimeout(() => {
    const r = [...document.querySelectorAll(".col")].map((c, i) => `col${i + 1}:${c.scrollHeight - c.clientHeight}`)
    const out = document.createElement("div")
    out.id = "overflow"
    out.hidden = true
    out.textContent = r.join(" ")
    document.body.appendChild(out)
  }, 300)
})
