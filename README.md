# Chazz — Local AI Automotive Engineering Assistant 🏎️🔧

**Chazz** is a locally hosted, domain-specific conversational AI assistant designed for automotive mechanics, ECU tuning diagnostics, gear-ratio calculations, and forced-induction troubleshooting. Built to run completely offline without cloud API dependencies.

---

### 🛠️ Technical Architecture
* **Inference Engine:** [Ollama](https://ollama.com) (Local Runtime)
* **Base Foundation Model:** Mistral (7B)
* **Core Logic:** Custom system prompt engineering, deterministic technical guardrails, and domain-specific context conditioning.

---

### ⚙️ Key Capabilities
* **ECU & Fuel/Boost Mapping Logic:** Assists with theoretical air-fuel ratio (AFR) targets, ignition timing concepts, and turbocharger spool dynamics.
* **Drivetrain & Gear Ratio Analysis:** Evaluates transmission gearing, final drive setups, and slip-angle/weight-transfer fundamentals.
* **Offline & Privacy-First Execution:** Runs 100% locally on consumer hardware with zero external telemetry or cloud latency.

---

### 🚀 Setup & Local Execution
1. Install **Ollama** on your local machine.
2. Pull the base Mistral model:
   ```bash
   ollama pull mistral
   ```
3. Run the custom `Modelfile` configuration to initialize the **Chazz** automotive engineering persona:
   ```bash
   ollama create chazz -f Modelfile
   ollama run chazz
   ```
