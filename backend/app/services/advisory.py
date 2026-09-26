from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

try:
    from langchain_core.documents import Document
    from langchain_community.retrievers import BM25Retriever
    LANGCHAIN_AVAILABLE = True
except Exception:  # Graceful demo fallback when optional LangChain deps are not installed yet.
    from dataclasses import dataclass, field
    @dataclass
    class Document:
        page_content: str
        metadata: dict = field(default_factory=dict)
    BM25Retriever = None
    LANGCHAIN_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parents[1]
KB_DIR = BASE_DIR / 'kb'


def load_kb_documents() -> list[Document]:
    docs: list[Document] = []
    for path in KB_DIR.glob('*'):
        if path.suffix.lower() not in {'.md', '.json', '.txt'}:
            continue
        text = path.read_text(encoding='utf-8')
        docs.append(Document(page_content=text, metadata={'source': path.name}))
    return docs


def retrieve_context(query: str, k: int = 4) -> list[Document]:
    docs = load_kb_documents()
    if LANGCHAIN_AVAILABLE and BM25Retriever is not None:
        retriever = BM25Retriever.from_documents(docs)
        retriever.k = min(k, len(docs))
        return retriever.invoke(query)

    # Dependency-free fallback used only when LangChain/rank_bm25 has not been installed.
    # Production/demo setup via requirements.txt uses LangChain BM25 retrieval.
    terms = {t.strip('.,:;()').lower() for t in query.split() if len(t) > 2}
    scored = []
    for doc in docs:
        text = doc.page_content.lower()
        score = sum(text.count(term) for term in terms)
        scored.append((score, doc))
    return [doc for _, doc in sorted(scored, key=lambda x: x[0], reverse=True)[:k]]


def build_structured_fallback(category: str, location: dict[str, Any], geo: dict[str, Any], finance: dict[str, Any]) -> dict[str, Any]:
    """Deterministic narrative fallback when no LLM key is configured."""
    competitors = geo['competitor_mapping']['competitors_within_10km']
    consumers = geo['consumer_base_estimate']['within_10km']
    income = geo['demographics'].get('monthly_household_income_proxy', 14000)

    cat = category.lower()
    category_hints = {
        'dairy': {
            'opportunities': ['Home-delivered milk subscriptions', 'Curd/paneer value addition', 'Tea stalls and small eateries as repeat B2B buyers'],
            'threats': ['Feed-price volatility', 'Animal health and cold-chain failures', 'Morning/evening demand concentration'],
            'pricing': 'Use a local benchmark band of ₹54–₹66/litre for standard milk, then validate with actual cooperative/private dairy prices.',
        },
        'retail': {
            'opportunities': ['Daily-use essentials with small pack sizes', 'UPI-enabled assisted ordering', 'School and SHG-linked repeat demand'],
            'threats': ['Thin margins', 'Inventory expiry', 'Competition from weekly markets and larger kirana stores'],
            'pricing': 'Prioritize low-ticket packs and maintain visible MRP/discount transparency.',
        },
        'textiles': {
            'opportunities': ['School uniforms', 'Festival-season garments', 'Alteration and repair services'],
            'threats': ['Seasonality', 'Dead inventory', 'Price competition from town wholesalers'],
            'pricing': 'Use good-better-best price ladders and keep entry SKUs aligned with local household income.',
        },
    }
    hints = category_hints.get(cat, {
        'opportunities': ['Bundle a core product with a repeat service', 'Sell through SHGs/local retailers', 'Target unmet convenience needs within 5–10 km'],
        'threats': ['Supply delays', 'Seasonal demand', 'Single-buyer dependency'],
        'pricing': 'Start with local competitor benchmarks and test small price bands before scaling inventory.',
    })

    swot = {
        'strengths': [f'Access to an estimated {consumers:,} consumers within 10 km', 'Low-distance local distribution can reduce last-mile cost', 'Scheme-linked capital can support initial productive assets'],
        'weaknesses': ['First-time operator execution risk', 'Limited working-capital buffer if all margin is used upfront', 'Mock data must be replaced by live local validation before lending'],
        'opportunities': hints['opportunities'],
        'threats': hints['threats'],
    }

    return {
        'mode': 'deterministic_demo_fallback',
        'headline': f'{category.title()} feasibility snapshot for {location["name"]}',
        'market_reach': f'Estimated addressable consumer base is about {consumers:,} people within 10 km. Use SHGs, local retailers, weekly haats, and repeat institutional buyers where available.',
        'opportunity_analysis': hints['opportunities'],
        'swot': swot,
        'threats': hints['threats'],
        'competitor_summary': f'{competitors} mapped {category} competitor(s) were found within 10 km in the demo POI dataset; density is {geo["competitor_mapping"]["density_label"].lower()}.',
        'product_market_value': hints['pricing'] + f' Household monthly income proxy in the demo dataset is ₹{income:,}.',
        'financial_guardrail': f'All financial numbers shown separately are computed by the deterministic engine; advisory text does not calculate loan eligibility or repayment values.',
    }


def _llm_advisory(provider: str, context: str, payload: dict[str, Any]) -> str | None:
    system = (
        'You are UDYAM MARG, a rural micro-enterprise advisory assistant. '
        'Use only the supplied context and structured facts. Never calculate or alter financial numbers. '
        'Return concise JSON with keys: market_reach, opportunity_analysis, swot (strengths, weaknesses, opportunities, threats), threats, competitor_summary, product_market_value. '
        'Be explicit that mock datasets are indicative, not lending evidence.'
    )
    user = f'RETRIEVED CONTEXT:\n{context}\n\nSTRUCTURED FACTS:\n{json.dumps(payload, ensure_ascii=False)}'

    try:
        if provider == 'openai' and os.getenv('OPENAI_API_KEY'):
            from langchain_openai import ChatOpenAI
            model = ChatOpenAI(model=os.getenv('OPENAI_MODEL', 'gpt-4.1-mini'), temperature=0.2)
            return model.invoke([('system', system), ('human', user)]).content
        if provider == 'gemini' and os.getenv('GOOGLE_API_KEY'):
            from langchain_google_genai import ChatGoogleGenerativeAI
            model = ChatGoogleGenerativeAI(model=os.getenv('GEMINI_MODEL', 'gemini-2.0-flash'), temperature=0.2)
            return model.invoke([('system', system), ('human', user)]).content
    except Exception:
        return None
    return None


def generate_advisory(category: str, location: dict[str, Any], geo: dict[str, Any], finance: dict[str, Any]) -> dict[str, Any]:
    query = f'{category} rural enterprise market pricing SWOT scheme local competition'
    retrieved = retrieve_context(query)
    context = '\n\n'.join(f'[{d.metadata.get("source")}] {d.page_content}' for d in retrieved)

    payload = {
        'category': category,
        'location': location,
        'geo_analysis': geo,
        # Only pass precomputed deterministic financial facts; LLM must not derive them.
        'financial_facts': {
            'project_cost': finance.get('project_cost'),
            'sanctionable_loan': finance.get('sanctionable_loan'),
            'scheme': finance.get('scheme'),
        },
    }
    provider = os.getenv('LLM_PROVIDER', 'none').lower()
    response = _llm_advisory(provider, context, payload)
    if response:
        try:
            parsed = json.loads(response.strip().removeprefix('```json').removesuffix('```').strip())
            parsed['mode'] = f'llm_rag_{provider}'
            parsed['retrieved_sources'] = [d.metadata.get('source') for d in retrieved]
            return parsed
        except Exception:
            fallback = build_structured_fallback(category, location, geo, finance)
            fallback['llm_raw_text'] = response
            fallback['retrieved_sources'] = [d.metadata.get('source') for d in retrieved]
            return fallback

    fallback = build_structured_fallback(category, location, geo, finance)
    fallback['retrieved_sources'] = [d.metadata.get('source') for d in retrieved]
    return fallback
