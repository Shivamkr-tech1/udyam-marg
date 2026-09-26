import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  MapPin, IndianRupee, BriefcaseBusiness, Mic, Volume2, WifiOff,
  ShieldCheck, Users, Store, TrendingUp, TriangleAlert, Landmark,
  ChevronDown, ChevronUp, Sparkles
} from 'lucide-react';
import './styles.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const CACHE_KEY = 'udyam-marg:last-analysis:v1';

const copy = {
  en: {
    title: 'UDYAM MARG',
    subtitle: 'Local business guidance + loan planning',
    location: 'Village / Block / District',
    margin: 'Your available margin capital',
    business: 'Business category',
    analyze: 'Check My Business',
    listening: 'Listening…',
    offline: 'Showing your last saved result',
    feasibility: 'Business Feasibility',
    finance: 'Loan & Repayment',
    credit: 'Alternative Credit Signal',
    projectCost: 'Project Cost',
    loan: 'Eligible Loan',
    scheme: 'Scheme',
    consumers: 'Consumers within 10 km',
    competitors: 'Nearby competitors',
    swot: 'SWOT',
    pricing: 'Pricing suggestion',
    schedule: 'Quarterly repayment schedule',
  },
  hi: {
    title: 'उद्यम मार्ग',
    subtitle: 'स्थानीय व्यवसाय मार्गदर्शन + ऋण योजना',
    location: 'गाँव / प्रखंड / जिला',
    margin: 'आपकी उपलब्ध मार्जिन पूंजी',
    business: 'व्यवसाय श्रेणी',
    analyze: 'मेरा व्यवसाय जाँचें',
    listening: 'सुन रहा है…',
    offline: 'पिछला सहेजा गया परिणाम दिखाया जा रहा है',
    feasibility: 'व्यवसाय व्यवहार्यता',
    finance: 'ऋण और पुनर्भुगतान',
    credit: 'वैकल्पिक क्रेडिट संकेत',
    projectCost: 'परियोजना लागत',
    loan: 'योग्य ऋण',
    scheme: 'योजना',
    consumers: '10 किमी में उपभोक्ता',
    competitors: 'आस-पास प्रतिस्पर्धी',
    swot: 'SWOT',
    pricing: 'मूल्य सुझाव',
    schedule: 'त्रैमासिक पुनर्भुगतान',
  }
};

const formatINR = (n) => new Intl.NumberFormat('en-IN', {
  style: 'currency', currency: 'INR', maximumFractionDigits: 0
}).format(n || 0);

function App() {
  const [lang, setLang] = useState('en');
  const t = copy[lang];
  const [form, setForm] = useState({
    location: 'Maner, Patna, Bihar',
    margin_capital: '100000',
    business_category: 'Dairy',
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [offlineCache, setOfflineCache] = useState(false);
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [listening, setListening] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem(CACHE_KEY);
    if (saved) {
      try { setResult(JSON.parse(saved)); } catch {}
    }
  }, []);

  const speak = (text) => {
    if (!('speechSynthesis' in window)) return alert('Text-to-speech is not supported in this browser.');
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-IN';
    window.speechSynthesis.speak(utterance);
  };

  const startVoiceInput = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return alert('Browser speech recognition is unavailable. This button is the Bhashini STT integration point.');
    const recognition = new SpeechRecognition();
    recognition.lang = lang === 'hi' ? 'hi-IN' : 'en-IN';
    recognition.interimResults = false;
    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setForm((f) => ({ ...f, location: transcript }));
    };
    recognition.start();
  };

  const analyze = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setOfflineCache(false);
    try {
      const res = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, margin_capital: Number(form.margin_capital) }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Analysis failed');
      const data = await res.json();
      setResult(data);
      localStorage.setItem(CACHE_KEY, JSON.stringify(data));
    } catch (err) {
      const saved = localStorage.getItem(CACHE_KEY);
      if (saved) {
        setResult(JSON.parse(saved));
        setOfflineCache(true);
      } else {
        setError(err.message || 'Unable to reach backend');
      }
    } finally {
      setLoading(false);
    }
  };

  const narration = useMemo(() => {
    if (!result) return '';
    const f = result.financial;
    const a = result.advisory;
    return `${a.headline || 'UDYAM MARG analysis'}. Project cost ${formatINR(f.project_cost)}. Loan ${formatINR(f.sanctionable_loan)} under ${f.scheme?.name || 'scheme not available'}. ${a.market_reach || ''}`;
  }, [result]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="brand-row"><div className="logo-mark">उ</div><h1>{t.title}</h1></div>
          <p>{t.subtitle}</p>
        </div>
        <button className="language" onClick={() => setLang(lang === 'en' ? 'hi' : 'en')}>
          {lang === 'en' ? 'हिंदी' : 'English'}
        </button>
      </header>

      <main>
        <section className="hero-card">
          <div className="hero-copy">
            <span className="eyebrow"><Sparkles size={16}/> AI-assisted, numbers rule-based</span>
            <h2>Know the market before you invest.</h2>
            <p>Enter three details. UDYAM MARG maps nearby demand, competition and a scheme-linked repayment plan.</p>
          </div>

          <form className="input-grid" onSubmit={analyze}>
            <label className="field">
              <span><MapPin size={18}/>{t.location}</span>
              <div className="voice-field">
                <input value={form.location} onChange={e => setForm({...form, location:e.target.value})} />
                <button type="button" className={`icon-btn ${listening ? 'pulse' : ''}`} onClick={startVoiceInput} aria-label="Voice location input"><Mic size={20}/></button>
              </div>
            </label>
            <label className="field">
              <span><IndianRupee size={18}/>{t.margin}</span>
              <input inputMode="numeric" value={form.margin_capital} onChange={e => setForm({...form, margin_capital:e.target.value.replace(/\D/g,'')})} />
            </label>
            <label className="field">
              <span><BriefcaseBusiness size={18}/>{t.business}</span>
              <select value={form.business_category} onChange={e => setForm({...form, business_category:e.target.value})}>
                <option>Dairy</option><option>Retail</option><option>Textiles</option><option>Food</option><option>Agri Inputs</option>
              </select>
            </label>
            <button className="primary" disabled={loading}>{loading ? 'Analyzing local data…' : t.analyze}</button>
          </form>
        </section>

        {offlineCache && <div className="offline-banner"><WifiOff size={18}/>{t.offline}</div>}
        {error && <div className="error-banner"><TriangleAlert size={18}/>{error}</div>}

        {result && <Results result={result} t={t} speak={() => speak(narration)} scheduleOpen={scheduleOpen} setScheduleOpen={setScheduleOpen} />}
      </main>

      <footer>
        Prototype data is indicative. Live Census/OSM/Bhashini/credit APIs are intentionally mocked for the SIH demo.
      </footer>
    </div>
  );
}

function Metric({icon:Icon, label, value, note}) {
  return <div className="metric"><div className="metric-icon"><Icon size={20}/></div><div><span>{label}</span><strong>{value}</strong>{note && <small>{note}</small>}</div></div>
}

function Results({result, t, speak, scheduleOpen, setScheduleOpen}) {
  const f = result.financial;
  const g = result.geospatial;
  const a = result.advisory;
  const c = result.alternative_creditworthiness;
  return <div className="results">
    <div className="result-heading"><div><span className="eyebrow">{result.location.name}</span><h2>Your enterprise snapshot</h2></div><button className="secondary" onClick={speak}><Volume2 size={18}/> Listen</button></div>

    <section className="panel">
      <div className="section-title"><Landmark size={22}/><div><h3>{t.finance}</h3><p>Computed only by deterministic Python rules</p></div><span className="verified"><ShieldCheck size={16}/> Rule-based</span></div>
      <div className="metric-grid">
        <Metric icon={IndianRupee} label={t.projectCost} value={formatINR(f.project_cost)} note={`Margin: ${formatINR(f.margin_capital)}`} />
        <Metric icon={Landmark} label={t.loan} value={formatINR(f.sanctionable_loan)} note="90% subject to scheme ceiling" />
        <Metric icon={ShieldCheck} label={t.scheme} value={f.scheme?.name || 'Outside scheme'} note={f.scheme ? `${f.scheme.annual_interest_rate}% • ${f.scheme.tenure_years} years • ${f.scheme.moratorium_months}-month moratorium` : f.reason} />
      </div>
      {f.repayment && <div className="schedule-wrap">
        <button className="schedule-toggle" onClick={() => setScheduleOpen(!scheduleOpen)}>
          <span><strong>{t.schedule}</strong><small>Approx. {formatINR(f.repayment.quarterly_payment_estimate)} / quarter after moratorium</small></span>
          {scheduleOpen ? <ChevronUp/> : <ChevronDown/>}
        </button>
        {scheduleOpen && <div className="table-scroll"><table><thead><tr><th>#</th><th>Due</th><th>Opening</th><th>Interest</th><th>Principal</th><th>Payment</th><th>Closing</th></tr></thead><tbody>
          {f.repayment.schedule.map(row => <tr key={row.installment_no}><td>{row.installment_no}</td><td>{row.due_date}</td><td>{formatINR(row.opening_principal)}</td><td>{formatINR(row.interest)}</td><td>{formatINR(row.principal_component)}</td><td>{formatINR(row.quarterly_payment)}</td><td>{formatINR(row.closing_principal)}</td></tr>)}
        </tbody></table></div>}
        <p className="fineprint">Assumption: {f.repayment.assumption}</p>
      </div>}
    </section>

    <section className="panel">
      <div className="section-title"><TrendingUp size={22}/><div><h3>{t.feasibility}</h3><p>{a.mode?.startsWith('llm') ? 'RAG + LLM narrative' : 'Local RAG context + deterministic demo narrative'}</p></div></div>
      <div className="metric-grid">
        <Metric icon={Users} label={t.consumers} value={g.consumer_base_estimate.within_10km.toLocaleString('en-IN')} note={`${g.consumer_base_estimate.within_5km.toLocaleString('en-IN')} within 5 km`} />
        <Metric icon={Store} label={t.competitors} value={`${g.competitor_mapping.competitors_within_10km}`} note={`${g.competitor_mapping.density_label} density`} />
        <Metric icon={MapPin} label="Mapped POIs" value={`${g.poi_counts.within_10km}`} note={`${g.h3_demand_zones.length} H3-style demand cells`} />
      </div>
      <div className="narrative-grid">
        <article><h4>Market reach</h4><p>{a.market_reach}</p></article>
        <article><h4>Opportunity</h4><ul>{(a.opportunity_analysis || []).map((x,i)=><li key={i}>{x}</li>)}</ul></article>
        <article className="wide"><h4>{t.pricing}</h4><p>{a.product_market_value}</p></article>
      </div>
      <h4 className="subhead">{t.swot}</h4>
      <div className="swot-grid">
        {Object.entries(a.swot || {}).map(([k,v]) => <div className={`swot ${k}`} key={k}><strong>{k}</strong><ul>{v.map((x,i)=><li key={i}>{x}</li>)}</ul></div>)}
      </div>
      <div className="competitor-list"><h4>Nearest mapped competitors</h4>{g.competitor_mapping.nearest.length ? g.competitor_mapping.nearest.map(p => <div className="competitor" key={p.id}><span>{p.name}</span><strong>{p.distance_km} km</strong></div>) : <p>No same-category competitor in the mock 10 km dataset.</p>}</div>
    </section>

    <section className="panel credit-panel">
      <div className="section-title"><ShieldCheck size={22}/><div><h3>{t.credit}</h3><p>Mock feature-based module — never a real bureau score</p></div></div>
      <div className="credit-score"><strong>{c.score_300_900}</strong><span>/ 900</span><em>{c.band}</em></div>
      <div className="credit-bars">
        {Object.entries(c.sample_features).map(([k,v]) => <div key={k}><span>{k.replaceAll('_',' ')}</span><div className="bar"><i style={{width:`${v*100}%`}}/></div><strong>{Math.round(v*100)}%</strong></div>)}
      </div>
      <p className="fineprint">{c.explanation}</p>
    </section>
  </div>
}

createRoot(document.getElementById('root')).render(<App />);
