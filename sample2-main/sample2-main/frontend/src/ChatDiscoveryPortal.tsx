import React, { useMemo, useState } from 'react';

type Sensitivity = 'High' | 'Medium' | 'Low';

type ChatMessage = {
  id: number;
  code: string;
  scenario: string;
  subject: string;
  from: string;
  channel: string;
  source: string;
  sensitivity: Sensitivity;
  date: string;
  attachment: string;
  content: string;
};

type AdvFilters = {
  subject: string;
  sender: string;
  attachment: string;
  sensitivity: '' | Sensitivity;
  from: string;
  to: string;
  hasAttachment: boolean;
};

type ChatDiscoveryWorkItem = {
  work_item_id: string;
  label: string;
  work_item: string;
  customer_request_id: string;
};
const CHANNELS = ['Support Channel', 'Sales Channel', 'Billing Channel', 'Escalation Channel'];
const FEEDS = ['Teams', 'Slack', 'WhatsApp', 'SMS'];
const SCENARIO_CHATS: ChatMessage[] = [
  {
    id: 101, code: 'CH001', scenario: 'Address Change', subject: "Address change for order SO-78110",
    from: 'neha.kapoor@acmeretail.com', channel: 'Support Channel', source: 'WhatsApp', sensitivity: 'Medium', date: '2026-10-01', attachment: '',
    content: "Customer: Hi, we shifted our store. Can you change the delivery address for SO-78110? Agent: Sure, please share the new address. Customer: Shop 7, MG Road, Bengaluru 560001. Agent: Noted, I will update it before dispatch.",
  },
  {
    id: 102, code: 'CH002', scenario: 'SPOC Change', subject: "New SPOC for Northwind account",
    from: 'anita.desai@northwind.com', channel: 'Sales Channel', source: 'Teams', sensitivity: 'Low', date: '2026-10-02', attachment: '',
    content: "Customer: Rahul has moved to another team, I am the new point of contact for all orders. Agent: Thanks Anita, can you confirm your phone number? Customer: +91 98450 11223. Agent: Updated, you will receive all future order communication.",
  },
  {
    id: 103, code: 'CH003', scenario: 'Delivery Date Change', subject: "Move delivery for SO-78204 to next week",
    from: 'kevin.lee@brightlabs.io', channel: 'Support Channel', source: 'Slack', sensitivity: 'Medium', date: '2026-10-03', attachment: '',
    content: "Customer: Our receiving dock is closed on 22 October. Can SO-78204 be delivered on 29 October instead? Agent: Let me check with logistics. Agent: Confirmed, the new delivery date is 29 October.",
  },
  {
    id: 104, code: 'CH004', scenario: 'Cancel Order', subject: "Please cancel SO-78231",
    from: 'maria.gomez@globex.com', channel: 'Escalation Channel', source: 'Teams', sensitivity: 'High', date: '2026-10-04', attachment: '',
    content: "Customer: We need to cancel SO-78231 urgently, the budget was withdrawn. Agent: The order is packed but not shipped. I can cancel it now. Customer: Please do, and confirm there is no penalty. Agent: Cancellation raised, confirmation will follow by email.",
  },
  {
    id: 105, code: 'CH005', scenario: 'New Order Creation', subject: "Place new order for 50 barcode scanners",
    from: 'procurement@initech.com', channel: 'Sales Channel', source: 'Teams', sensitivity: 'Medium', date: '2026-10-05', attachment: 'PO-46122.pdf',
    content: "Customer: We want to order 50 handheld barcode scanners. PO attached. Agent: Received PO-46122. Delivery address is your Chennai warehouse? Customer: Yes. Agent: Order created, confirmation number will be shared shortly.",
  },
  {
    id: 106, code: 'CH006', scenario: 'Invoice Request', subject: "Need invoice for SO-77890",
    from: 'accounts@umbrella-corp.com', channel: 'Billing Channel', source: 'SMS', sensitivity: 'Medium', date: '2026-10-06', attachment: '',
    content: "Customer: We have not received the invoice for SO-77890. Agent: I can see it was generated yesterday. Customer: Please resend to accounts@umbrella-corp.com. Agent: Sent, please check your inbox.",
  },
  {
    id: 107, code: 'CH007', scenario: 'Status Request', subject: "Where is my order SO-78012?",
    from: 'li.wei@starkindustries.com', channel: 'Support Channel', source: 'WhatsApp', sensitivity: 'Low', date: '2026-10-07', attachment: '',
    content: "Customer: Any update on SO-78012? Tracking has not moved. Agent: It is at the Mumbai hub and is scheduled for delivery tomorrow by 6 PM. Customer: Great, thanks.",
  },
  {
    id: 108, code: 'CH008', scenario: 'Delivery Issue', subject: "Wrong items delivered in SO-77955",
    from: 'ops@wayneenterprises.com', channel: 'Escalation Channel', source: 'Slack', sensitivity: 'High', date: '2026-10-08', attachment: 'wrong_items_photo.jpg',
    content: "Customer: We received 15-inch monitors instead of 24-inch for SO-77955. Photo attached. Agent: Sorry about that. I will arrange a pickup and send the correct items. Customer: We need them by Friday. Agent: Marked as priority replacement.",
  },
  {
    id: 109, code: 'CH009', scenario: 'Quantity Change', subject: "Reduce quantity on PO-46001",
    from: 'sanjay.patel@cyberdyne.com', channel: 'Sales Channel', source: 'Teams', sensitivity: 'Medium', date: '2026-10-09', attachment: '',
    content: "Customer: Please reduce PO-46001 from 100 to 70 mouse units. Agent: The order has not been picked yet, so I can update it. Customer: Please also send a revised confirmation. Agent: Updated and revised confirmation is on the way.",
  },
  {
    id: 110, code: 'CH010', scenario: 'Invoice Correction', subject: "Invoice INV-2026-0950 has wrong unit price",
    from: 'finance@oceanic-airlines.com', channel: 'Billing Channel', source: 'Teams', sensitivity: 'High', date: '2026-10-10', attachment: 'INV-2026-0950.pdf',
    content: "Customer: INV-2026-0950 shows a unit price of 4,500 but the agreed price is 4,200. Agent: I can see the contract price is 4,200. I will raise a correction. Customer: Please send the credit note too. Agent: Correction request raised with Finance.",
  },
];
const EMPTY_ADV: AdvFilters = { subject: '', sender: '', attachment: '', sensitivity: '', from: '', to: '', hasAttachment: false };
const BADGE: Record<Sensitivity, string> = { High: '#ef4444', Medium: '#f59e0b', Low: '#10b981' };
const has = (v: string, q: string) => !q || v.toLowerCase().includes(q.toLowerCase());
const toggle = (list: string[], x: string) => (list.includes(x) ? list.filter((i) => i !== x) : [...list, x]);

const CSS = `
*{box-sizing:border-box}
.cdp{min-height:100vh;background:#f1f5f9;font-family:"Segoe UI",system-ui,sans-serif;color:#0f172a}
.cdp .hdr{background:#0f172a;color:#fff;display:flex;justify-content:space-between;align-items:center;padding:14px 24px;gap:16px;flex-wrap:wrap}
.cdp .hdr h2{margin:0;font-size:20px}
.cdp .row{display:flex;gap:8px;align-items:center}
.cdp .inp{padding:9px 12px;border:1px solid #cbd5e1;border-radius:8px;font:inherit;width:100%}
.cdp .hdr .inp{width:300px;border:none}
.cdp .btn{padding:9px 14px;border:none;border-radius:8px;cursor:pointer;font:inherit;font-weight:600;background:#e2e8f0;color:#0f172a;transition:.15s}
.cdp .btn:hover{filter:brightness(.92)}.cdp .btn:disabled{opacity:.5;cursor:not-allowed}
.cdp .pri{background:#2563eb;color:#fff}.cdp .dot{background:#f59e0b;border-radius:50%;width:8px;height:8px;display:inline-block;margin-left:6px}
.cdp{container-type:inline-size}
.cdp .main{display:grid;grid-template-columns:220px minmax(0,1fr) 340px;align-items:start;gap:16px;padding:16px}
.cdp .main>section{position:sticky;top:16px}
.cdp td:nth-child(1),.cdp td:nth-child(5),.cdp td:nth-child(6),.cdp .badge{white-space:nowrap}
.cdp td:nth-child(1){font-weight:600}
@container (max-width:1200px){
.cdp .main{grid-template-columns:minmax(0,1fr) 320px}
.cdp .main>aside{grid-column:1/-1;display:grid;grid-template-columns:1fr 1fr auto;gap:8px 24px;align-items:start}
.cdp .main>aside hr{display:none}
.cdp .main>aside>.btn{margin-top:0!important;width:auto!important;align-self:center}
.cdp .grp{display:flex;flex-wrap:wrap;gap:0 12px}.cdp .grp>.row{flex-basis:100%}.cdp .grp h3{margin-bottom:4px}
}
@container (max-width:760px){
.cdp .main{grid-template-columns:minmax(0,1fr)}
.cdp .main>aside{grid-template-columns:1fr}
.cdp .main>section{position:static}
.cdp .main>main{display:contents}
.cdp .main>main>.stats{order:1;margin-bottom:0}.cdp .main>section{order:2}.cdp .main>main>.card{order:3}
}
.cdp .card{background:#fff;border-radius:12px;padding:18px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.cdp .card h3{margin:0 0 12px;font-size:16px}
.cdp .chk{display:flex;align-items:center;gap:8px;padding:6px 4px;border-radius:6px;cursor:pointer}
.cdp .chk:hover{background:#f1f5f9}.cdp .chk span{flex:1}
.cdp .x{background:none;border:none;color:#94a3b8;cursor:pointer;font-size:16px}.cdp .x:hover{color:#ef4444}
.cdp .link{background:none;border:none;color:#2563eb;cursor:pointer;font-size:12px;padding:0}
.cdp .stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px}
.cdp .stat{color:#fff;padding:14px 16px;border-radius:12px}.cdp .stat p{margin:0;opacity:.85;font-size:13px}.cdp .stat b{font-size:28px}
.cdp table{width:100%;border-collapse:collapse}.cdp th{text-align:left;font-size:12px;color:#64748b;text-transform:uppercase;padding:8px}
.cdp td{padding:10px 8px;border-top:1px solid #f1f5f9}.cdp tbody tr{cursor:pointer}.cdp tbody tr:hover{background:#f8fafc}
.cdp tr.sel{background:#eff6ff!important}
.cdp .badge{color:#fff;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600}
.cdp .muted{color:#64748b;font-size:14px}.cdp .meta p{margin:6px 0;font-size:14px}
.cdp .ov{position:fixed;inset:0;background:rgba(15,23,42,.5);display:flex;justify-content:center;align-items:center}
.cdp .modal{width:440px;background:#fff;border-radius:12px;padding:22px;display:grid;gap:10px}
.cdp .modal h3{margin:0}.cdp .lbl{font-size:12px;color:#64748b}
.cdp .err{color:#ef4444;font-size:13px}
`;

type CheckListProps = {
  title: string;
  items: string[];
  sel: string[];
  setSel: (items: string[]) => void;
  onRemove?: (item: string) => void;
};

function CheckList({ title, items, sel, setSel, onRemove }: CheckListProps) {
  return (
    <>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h3>{title}</h3>
        <button className="link" onClick={() => setSel(sel.length === items.length ? [] : items)}>
          {sel.length === items.length ? 'None' : 'All'}
        </button>
      </div>
      {items.map((i) => (
        <label key={i} className="chk">
          <input type="checkbox" checked={sel.includes(i)} onChange={() => setSel(toggle(sel, i))} />
          <span>{i}</span>
          {onRemove && !FEEDS.includes(i) && (
            <button className="x" title="Remove feed" onClick={(e) => { e.preventDefault(); onRemove(i); }}>×</button>
          )}
        </label>
      ))}
    </>
  );
}

export default function ChatDiscoveryPortal({ workItem }: { workItem: ChatDiscoveryWorkItem }) {
  const [searchText, setSearchText] = useState('');
  const [query, setQuery] = useState('');
  const [adv, setAdv] = useState<AdvFilters>(EMPTY_ADV);
  const [draft, setDraft] = useState<AdvFilters>(EMPTY_ADV);
  const [feeds, setFeeds] = useState<string[]>(FEEDS);
  const [selChannels, setSelChannels] = useState<string[]>(CHANNELS);
  const [selSources, setSelSources] = useState<string[]>(FEEDS);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [modal, setModal] = useState<'adv' | 'feed' | null>(null);
  const [newFeed, setNewFeed] = useState('');
  const messagesForWork = useMemo<ChatMessage[]>(() => [{
    id: 1,
    code: workItem.customer_request_id,
    scenario: 'Current Work Item',
    subject: workItem.work_item,
    from: 'customer@local.dev',
    channel: 'Support Channel',
    source: 'Teams',
    sensitivity: 'Medium',
    date: '2026-10-08',
    attachment: '',
    content: `Chat conversation about ${workItem.work_item}. Request ${workItem.customer_request_id} needs the next step confirmed.`,
  }, ...SCENARIO_CHATS], [workItem]);

  const messages = useMemo(
    () =>
      messagesForWork.filter(
        (m) =>
          selChannels.includes(m.channel) &&
          selSources.includes(m.source) &&
          (has(m.subject, query) || has(m.content, query) || has(m.from, query) || has(m.code, query) || has(m.scenario, query)) &&
          has(m.subject, adv.subject) &&
          has(m.from, adv.sender) &&
          has(m.attachment || '', adv.attachment) &&
          (!adv.sensitivity || m.sensitivity === adv.sensitivity) &&
          (!adv.hasAttachment || !!m.attachment) &&
          (!adv.from || m.date >= adv.from) &&
          (!adv.to || m.date <= adv.to)
      ),
    [messagesForWork, selChannels, selSources, query, adv]
  );
  const selected = messages.find((m) => m.id === selectedId);
  const advActive = JSON.stringify(adv) !== JSON.stringify(EMPTY_ADV);

  const search = () => {
    setQuery(searchText.trim());
    setSelectedId(null);
  };
  const reset = () => {
    setSearchText(''); setQuery(''); setAdv(EMPTY_ADV); setDraft(EMPTY_ADV);
    setSelChannels(CHANNELS); setSelSources(feeds); setSelectedId(null);
  };
  const feedName = newFeed.trim();
  const feedDup = feeds.some((f) => f.toLowerCase() === feedName.toLowerCase());
  const saveFeed = () => {
    if (!feedName || feedDup) return;
    setFeeds([...feeds, feedName]);
    setSelSources([...selSources, feedName]);
    setNewFeed(''); setModal(null);
  };
  const removeFeed = (f: string) => {
    setFeeds(feeds.filter((x) => x !== f));
    setSelSources(selSources.filter((x) => x !== f));
  };
  const setD = (k: keyof AdvFilters) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const value = e.target.type === 'checkbox' ? (e.target as HTMLInputElement).checked : e.target.value;
    setDraft({ ...draft, [k]: value });
  };

  return (
    <div className="cdp">
      <style>{CSS}</style>

      <header className="hdr">
        <h2>Chat Discovery Portal</h2>
        <div className="row">
          <input className="inp" placeholder="Search subject, content, sender..." value={searchText}
            onChange={(e) => setSearchText(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && search()} />
          <button className="btn pri" onClick={search}>Search</button>
          <button className="btn" onClick={reset}>Reset</button>
          <button className="btn" onClick={() => { setDraft(adv); setModal('adv'); }}>
            Advanced{advActive && <span className="dot" />}
          </button>
        </div>
      </header>

      <div className="main">
        <aside className="card">
          <div className="grp"><CheckList title="💬 Channels" items={CHANNELS} sel={selChannels} setSel={setSelChannels} /></div>
          <hr style={{ border: 0, borderTop: '1px solid #e2e8f0', margin: '16px 0' }} />
          <div className="grp"><CheckList title="🔗 Sources" items={feeds} sel={selSources} setSel={setSelSources} onRemove={removeFeed} /></div>
          <button className="btn pri" style={{ width: '100%', marginTop: 16 }} onClick={() => setModal('feed')}>+ Add Feed</button>
        </aside>

        <main>
          <div className="stats">
            <div className="stat" style={{ background: '#2563eb' }}><p>Total Chats</p><b>{messages.length}</b></div>
            <div className="stat" style={{ background: '#ef4444' }}><p>High Sensitivity</p><b>{messages.filter((m) => m.sensitivity === 'High').length}</b></div>
            <div className="stat" style={{ background: '#10b981' }}><p>Active Sources</p><b>{selSources.length}</b></div>
          </div>
          <div className="card">
            <h3>📋 Search Results</h3>
            {messages.length ? (
              <table>
                <thead><tr><th>ID</th><th>Scenario</th><th>Subject</th><th>Channel</th><th>Date</th><th>Sensitivity</th></tr></thead>
                <tbody>
                  {messages.map((m) => (
                    <tr key={m.id} className={m.id === selectedId ? 'sel' : ''} onClick={() => setSelectedId(m.id)}>
                      <td>{m.code}</td><td>{m.scenario}</td><td>{m.subject}</td><td>{m.channel}</td><td>{m.date}</td>
                      <td><span className="badge" style={{ background: BADGE[m.sensitivity] }}>{m.sensitivity}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="muted">No chats match your filters. <button className="link" onClick={reset}>Clear all filters</button></p>
            )}
          </div>
        </main>

        <section className="card">
          <h3>💬 Chat Preview</h3>
          {selected ? (
            <div className="meta">
              <h2 style={{ margin: '0 0 10px' }}>{selected.subject}</h2>
              <p><b>ID:</b> {selected.code}</p>
              <p><b>Scenario:</b> {selected.scenario}</p>
              <p><b>From:</b> {selected.from}</p>
              <p><b>Channel:</b> {selected.channel}</p>
              <p><b>Source:</b> {selected.source}</p>
              <p><b>Date:</b> {selected.date}</p>
              <p><b>Sensitivity:</b> <span className="badge" style={{ background: BADGE[selected.sensitivity] }}>{selected.sensitivity}</span></p>
              <hr /><p>{selected.content}</p><hr />
              {selected.attachment && <p>📎 {selected.attachment}</p>}
            </div>
          ) : (
            <p className="muted">Select a chat from search results.</p>
          )}
        </section>
      </div>

      {modal === 'adv' && (
        <div className="ov" onClick={() => setModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Advanced Search</h3>
            <input className="inp" placeholder="Subject" value={draft.subject} onChange={setD('subject')} />
            <input className="inp" placeholder="Sender" value={draft.sender} onChange={setD('sender')} />
            <input className="inp" placeholder="Attachment name" value={draft.attachment} onChange={setD('attachment')} />
            <select className="inp" value={draft.sensitivity} onChange={setD('sensitivity')}>
              <option value="">All sensitivities</option><option>High</option><option>Medium</option><option>Low</option>
            </select>
            <div className="row">
              <div style={{ flex: 1 }}><span className="lbl">From</span><input className="inp" type="date" value={draft.from} max={draft.to || undefined} onChange={setD('from')} /></div>
              <div style={{ flex: 1 }}><span className="lbl">To</span><input className="inp" type="date" value={draft.to} min={draft.from || undefined} onChange={setD('to')} /></div>
            </div>
            <label className="chk"><input type="checkbox" checked={draft.hasAttachment} onChange={setD('hasAttachment')} /> Has attachment</label>
            <div className="row" style={{ justifyContent: 'space-between', marginTop: 8 }}>
              <button className="btn" onClick={() => setDraft(EMPTY_ADV)}>Clear</button>
              <div className="row">
                <button className="btn" onClick={() => setModal(null)}>Cancel</button>
                <button className="btn pri" onClick={() => { setAdv(draft); setSelectedId(null); setModal(null); }}>Apply Filters</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {modal === 'feed' && (
        <div className="ov" onClick={() => setModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Add Feed</h3>
            <input className="inp" autoFocus placeholder="Feed name" value={newFeed}
              onChange={(e) => setNewFeed(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && saveFeed()} />
            {feedDup && feedName && <span className="err">Feed already exists.</span>}
            <div className="row" style={{ justifyContent: 'flex-end' }}>
              <button className="btn" onClick={() => { setNewFeed(''); setModal(null); }}>Cancel</button>
              <button className="btn pri" disabled={!feedName || feedDup} onClick={saveFeed}>Save Feed</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
