# UDYAM MARG — SIH Prototype

AI-assisted hyper-local business advisory + deterministic financial structuring for rural micro-entrepreneurs.

## What is implemented

- **React/Vite responsive frontend** with large touch targets, English/Hindi UI toggle, Web Speech API microphone stub, browser text-to-speech, and `localStorage` caching of the last successful result.
- **FastAPI backend** split into three main services:
  - `finance.py`: 100% deterministic 90:10 project-cost calculation, scheme routing, loan cap handling and quarterly repayment schedule.
  - `geo.py`: SQLite POI store, Haversine radius analysis, competitor density, consumer proxy and H3 demand-zone grouping (with a graceful conceptual fallback if `h3` is not installed).
  - `advisory.py`: local knowledge-base retrieval through LangChain BM25 when installed, optional OpenAI/Gemini generation, and a deterministic narrative fallback when no API key is provided.
- **Alternative creditworthiness stub** using synthetic utility/UPI/SHG features. It is clearly marked as non-production and is never used as a real lending score.
- **Realistic mock datasets** for POIs, demographics, pricing and scheme/advisory context.
- **Automated tests** for the requested sample flow and scheme edge cases.

## Architecture

```text
React / Vite Web
  ├─ large touch UI + Hindi/English labels
  ├─ Web Speech API stub (Bhashini integration point)
  └─ localStorage last-result cache
          │ HTTP JSON
          ▼
FastAPI
  ├─ Deterministic Finance Engine
  │    ├─ margin / 0.10
  │    ├─ 90% loan + scheme ceiling
  │    ├─ scheme router
  │    └─ quarterly moratorium-aware schedule
  ├─ Geospatial Engine
  │    ├─ SQLite mock POIs
  │    ├─ Haversine 5/10 km search
  │    └─ H3 demand cells
  ├─ RAG Advisory Engine
  │    ├─ local Markdown KB
  │    ├─ LangChain BM25 retrieval
  │    └─ optional OpenAI/Gemini narrative only
  └─ Mock Alternative Credit Score
```

## 1. Run the backend

Recommended: Python 3.11 or 3.12.

```bash
cd backend
python -m venv .venv
```

Activate it:

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS/Linux**

```bash
source .venv/bin/activate
```

Install and run:

```bash
pip install -r requirements.txt
cp .env.example .env       # Windows: copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs: `http://127.0.0.1:8000/docs`

### Optional LLM

The prototype works without an LLM key. In that mode, local KB retrieval still occurs and the final narrative uses a deterministic demo template.

For OpenAI, edit `backend/.env`:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=<your-supported-model>
```

For Gemini:

```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=...
GEMINI_MODEL=<your-supported-model>
```

The LLM receives **precomputed financial facts only**. It never performs project-cost, loan, scheme, interest, moratorium or repayment calculations.

## 2. Run the frontend

Open a second terminal:

```bash
cd frontend
npm install
copy .env.example .env     # Windows
# or: cp .env.example .env # macOS/Linux
npm run dev
```

Open `http://localhost:5173`.

## Requested demo flow

Use:

```text
Location: Maner, Patna, Bihar
Margin capital: 100000
Business: Dairy
```

Verified backend output:

```text
Project Cost: ₹10,00,000
90% / sanctionable loan: ₹9,00,000
Scheme: Term Loan Scheme
Interest: 8% p.a.
Tenure: 7 years
Moratorium: 6 months
Repayment periods: 26 quarterly installments
Indicative quarterly payment: ~₹46,549
```

The demo POI dataset currently finds 4 Dairy competitors within the sample 10 km area.

A complete example API payload is included as `sample_response.json`.

## Financial repayment assumption

For this prototype, **total scheme tenure includes the moratorium**. No installment is paid during the moratorium; interest accrues monthly and is capitalized. The remaining tenure is then amortized using equal quarterly installments.

This is intentionally isolated in `backend/app/services/finance.py`. If the official implementing-agency circular defines a different moratorium treatment, only that deterministic function should be changed; the LLM should never be used to resolve the calculation.

The Micro Finance edge case is also handled: at exactly ₹1.40 lakh project cost, 90% would be ₹1.26 lakh, but the stated scheme ceiling is ₹1.25 lakh, so the prototype exposes a ₹1,000 financing gap instead of silently exceeding the cap.

## Production vs demo/stub

| Component | Prototype status | Production replacement |
|---|---|---|
| 90:10 finance + scheme router | Implemented, deterministic | Validate against official/latest scheme circulars |
| Quarterly schedule | Implemented, deterministic | Align moratorium/interest treatment with lender rules |
| POI search | Implemented on mock SQLite data | PostGIS + OSM/Data.gov.in ingestion |
| H3 | Implemented when `h3` installed | Persistent multi-resolution H3 indexes |
| Consumer reach | Mock demographic proxy | Census/Data.gov.in population raster/ward/village data |
| RAG retrieval | Local KB + LangChain BM25 | Curated circulars, market datasets, versioned citations |
| LLM advisory | Optional OpenAI/Gemini | Guardrailed provider + structured outputs + audit logs |
| Bhashini | Web Speech browser stub | Bhashini STT/TTS APIs + vernacular prompt catalogue |
| Creditworthiness | Synthetic sample features | Consent-based regulated data + fairness/compliance review |
| Offline resilience | `localStorage` last result | Service worker + IndexedDB + sync queue |

## Tests

```bash
cd backend
pytest -q
```

The included tests cover:

- ₹1,00,000 margin → ₹10,00,000 project → ₹9,00,000 Term Loan route.
- ₹14,000 margin → ₹1,40,000 Micro Finance project with ₹1.25 lakh loan cap.
- Project cost above ₹50 lakh → outside the prototype scheme ceiling.
- Full `/api/analyze` response contains finance, geospatial and SWOT/advisory sections.

## Key files

```text
backend/app/main.py
backend/app/services/finance.py
backend/app/services/geo.py
backend/app/services/advisory.py
backend/app/services/credit.py
backend/app/data/
backend/app/kb/
backend/tests/
frontend/src/main.jsx
frontend/src/styles.css
```

## Important demo note

The scheme values in this prototype are implemented exactly from the problem statement supplied for the hackathon. Before any real deployment or lending decision, validate them against the current official scheme guidelines and implementing-agency rules.
