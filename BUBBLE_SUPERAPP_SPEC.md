# BUBBLE OS — FLUTTER SUPER APP SPECIFICATION

## 🏛️ SYSTEM ARCHITECTURE
```text
lib/
 ├── core/
 │    ├── auth/ (AEGIS)
 │    ├── finance/ (FCE)
 │    ├── shell/ (Chat UI)
 │
 ├── features/
 │    ├── chat/ (Conversational Transactions)
 │    ├── wallet/ (iMOXON Pay)
 │    ├── mini_apps/ (SDK Host)
 │
 ├── shared/
      ├── cards/ (Action Cards)
      ├── widgets/ (Theming)
```

## 🧠 CHAT-TO-TRANSACTION FLOW
1. **User:** "Order 50 bed sheets for resort."
2. **Intent Engine:** Detected `PROCUREMENT_REQUEST`.
3. **FCE Bridge:** Fetches pricing (MIRA compliant).
4. **UI Response:** Renders `Action Card` in chat stream.
5. **User Action:** Clicks `[CONFIRM]`.
6. **Execution:** Guard triggers backend workflow.

## 🧱 UI PRIMITIVES
- **Message:** Bubbles for text.
- **Card:** Self-contained mini-forms for data.
- **Confirm:** Multi-stage validation before execution.
