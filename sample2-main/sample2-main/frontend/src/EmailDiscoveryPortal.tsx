import React, { useMemo, useState } from 'react';

type Sensitivity = 'High' | 'Medium' | 'Low';

type MailEmail = {
  id: number;
  code: string;
  scenario: string;
  subject: string;
  from: string;
  mailbox: string;
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

type EmailDiscoveryWorkItem = {
  work_item_id: string;
  label: string;
  work_item: string;
  customer_request_id: string;
};
const MAILBOXES = ['HP Mailbox', 'HR Mailbox', 'Finance Mailbox', 'Legal Mailbox'];
const FEEDS = ['Exchange', 'Outlook', 'Teams', 'Shared Mailbox'];
const SCENARIO_EMAILS: MailEmail[] = [
  {
    id: 101, code: 'EM001', scenario: 'Address Change', subject: 'Change of delivery address for PO-45821',
    from: 'priya.nair@acmeretail.com', mailbox: 'HP Mailbox', source: 'Exchange', sensitivity: 'Medium', date: '2026-10-01', attachment: '',
    content: 'Hi team, we have moved our warehouse. Please update the delivery address for PO-45821 to Plot 14, Industrial Area Phase 2, Pune 411019 before dispatch. The old Hinjewadi address should no longer be used.',
  },
  {
    id: 102, code: 'EM002', scenario: 'SPOC Change', subject: 'Update to single point of contact - Northwind Traders',
    from: 'rahul.mehta@northwind.com', mailbox: 'HP Mailbox', source: 'Outlook', sensitivity: 'Low', date: '2026-10-02', attachment: '',
    content: 'Please note that effective immediately, Anita Desai (anita.desai@northwind.com, +91 98450 11223) will be our SPOC for all orders and invoices, replacing me. Kindly update your records and copy her on open requests.',
  },
  {
    id: 103, code: 'EM003', scenario: 'Delivery Date Change', subject: 'Request to reschedule delivery for order SO-77314',
    from: 'kevin.lee@brightlabs.io', mailbox: 'HP Mailbox', source: 'Exchange', sensitivity: 'Medium', date: '2026-10-03', attachment: '',
    content: 'Our site will be closed for maintenance during the week of 20 October. Could you move the delivery for SO-77314 from 21 October to 28 October? Please confirm the revised date.',
  },
  {
    id: 104, code: 'EM004', scenario: 'Cancel Order', subject: 'Cancellation of order SO-77402',
    from: 'maria.gomez@globex.com', mailbox: 'HP Mailbox', source: 'Shared Mailbox', sensitivity: 'High', date: '2026-10-04', attachment: 'Cancellation_Request_SO-77402.pdf',
    content: 'We need to cancel order SO-77402 (12 x thermal printers) because the project has been put on hold. Please stop shipment and confirm that no cancellation charges apply. The signed cancellation request is attached.',
  },
  {
    id: 105, code: 'EM005', scenario: 'New Order Creation', subject: 'New purchase order PO-46010 - laptop docking stations',
    from: 'procurement@initech.com', mailbox: 'HP Mailbox', source: 'Outlook', sensitivity: 'Medium', date: '2026-10-05', attachment: 'PO-46010.pdf',
    content: 'Please create a new order for 25 USB-C docking stations (model HP G5) against the attached PO-46010. Requested delivery is 15 November to our Bengaluru office. Kindly share the order confirmation.',
  },
  {
    id: 106, code: 'EM006', scenario: 'Invoice Request', subject: 'Request for invoice copy - SO-76988',
    from: 'accounts@umbrella-corp.com', mailbox: 'Finance Mailbox', source: 'Exchange', sensitivity: 'Medium', date: '2026-10-06', attachment: '',
    content: 'We received the delivery for SO-76988 but have not received the invoice. Please send a copy of the tax invoice so we can process the payment this month.',
  },
  {
    id: 107, code: 'EM007', scenario: 'Status Request', subject: 'Status of order SO-77150?',
    from: 'li.wei@starkindustries.com', mailbox: 'HP Mailbox', source: 'Teams', sensitivity: 'Low', date: '2026-10-07', attachment: '',
    content: 'Hi, could you share the current status of SO-77150? The tracking link has not been updated for three days and we need an ETA for our internal planning.',
  },
  {
    id: 108, code: 'EM008', scenario: 'Delivery Issue', subject: 'Damaged items received in shipment SO-77021',
    from: 'ops@wayneenterprises.com', mailbox: 'HP Mailbox', source: 'Exchange', sensitivity: 'High', date: '2026-10-08', attachment: 'Damaged_Goods_Photos.zip',
    content: 'Two of the ten monitors delivered under SO-77021 arrived with cracked screens, and one carton was missing. Photos are attached. Please arrange a replacement and raise a claim with the carrier.',
  },
  {
    id: 109, code: 'EM009', scenario: 'Quantity Change', subject: 'Increase quantity on PO-45990',
    from: 'sanjay.patel@cyberdyne.com', mailbox: 'HP Mailbox', source: 'Outlook', sensitivity: 'Medium', date: '2026-10-09', attachment: 'PO-45990_Rev1.pdf',
    content: 'We would like to increase the quantity on PO-45990 from 40 to 60 wireless keyboards. The revised PO is attached. Please confirm whether the original delivery date still holds.',
  },
  {
    id: 110, code: 'EM010', scenario: 'Invoice Correction', subject: 'Incorrect GST number on invoice INV-2026-0912',
    from: 'finance@oceanic-airlines.com', mailbox: 'Finance Mailbox', source: 'Shared Mailbox', sensitivity: 'High', date: '2026-10-10', attachment: 'INV-2026-0912.pdf',
    content: 'Invoice INV-2026-0912 shows an incorrect GSTIN and billing entity. The correct GSTIN is 27AABCO1234F1Z5 for Oceanic Airlines India Pvt Ltd. Please issue a credit note and a corrected invoice.',
  },
];
const EMPTY_ADV: AdvFilters = { subject: '', sender: '', attachment: '', sensitivity: '', from: '', to: '', hasAttachment: false };
const BADGE: Record<Sensitivity, string> = { High: '#ef4444', Medium: '#f59e0b', Low: '#10b981' };
const has = (v: string, q: string) => !q || v.toLowerCase().includes(q.toLowerCase());
const toggle = (list: string[], x: string) => (list.includes(x) ? list.filter((i) => i !== x) : [...list, x]);

const CSS = `
*{box-sizing:border-box}
.edp{min-height:100vh;background:#f1f5f9;font-family:"Segoe UI",system-ui,sans-serif;color:#0f172a}
.edp .hdr{background:#0f172a;color:#fff;display:flex;justify-content:space-between;align-items:center;padding:14px 24px;gap:16px;flex-wrap:wrap}
.edp .hdr h2{margin:0;font-size:20px}
.edp .row{display:flex;gap:8px;align-items:center}
.edp .inp{padding:9px 12px;border:1px solid #cbd5e1;border-radius:8px;font:inherit;width:100%}
.edp .hdr .inp{width:300px;border:none}
.edp .btn{padding:9px 14px;border:none;border-radius:8px;cursor:pointer;font:inherit;font-weight:600;background:#e2e8f0;color:#0f172a;transition:.15s}
.edp .btn:hover{filter:brightness(.92)}.edp .btn:disabled{opacity:.5;cursor:not-allowed}
.edp .pri{background:#2563eb;color:#fff}.edp .dot{background:#f59e0b;border-radius:50%;width:8px;height:8px;display:inline-block;margin-left:6px}
.edp{container-type:inline-size}
.edp .main{display:grid;grid-template-columns:220px minmax(0,1fr) 340px;align-items:start;gap:16px;padding:16px}
.edp .main>section{position:sticky;top:16px}
.edp td:nth-child(1),.edp td:nth-child(5),.edp td:nth-child(6),.edp .badge{white-space:nowrap}
.edp td:nth-child(1){font-weight:600}
@container (max-width:1200px){
.edp .main{grid-template-columns:minmax(0,1fr) 320px}
.edp .main>aside{grid-column:1/-1;display:grid;grid-template-columns:1fr 1fr auto;gap:8px 24px;align-items:start}
.edp .main>aside hr{display:none}
.edp .main>aside>.btn{margin-top:0!important;width:auto!important;align-self:center}
.edp .grp{display:flex;flex-wrap:wrap;gap:0 12px}.edp .grp>.row{flex-basis:100%}.edp .grp h3{margin-bottom:4px}
}
@container (max-width:760px){
.edp .main{grid-template-columns:minmax(0,1fr)}
.edp .main>aside{grid-template-columns:1fr}
.edp .main>section{position:static}
.edp .main>main{display:contents}
.edp .main>main>.stats{order:1;margin-bottom:0}.edp .main>section{order:2}.edp .main>main>.card{order:3}
}
.edp .card{background:#fff;border-radius:12px;padding:18px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.edp .card h3{margin:0 0 12px;font-size:16px}
.edp .chk{display:flex;align-items:center;gap:8px;padding:6px 4px;border-radius:6px;cursor:pointer}
.edp .chk:hover{background:#f1f5f9}.edp .chk span{flex:1}
.edp .x{background:none;border:none;color:#94a3b8;cursor:pointer;font-size:16px}.edp .x:hover{color:#ef4444}
.edp .link{background:none;border:none;color:#2563eb;cursor:pointer;font-size:12px;padding:0}
.edp .stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px}
.edp .stat{color:#fff;padding:14px 16px;border-radius:12px}.edp .stat p{margin:0;opacity:.85;font-size:13px}.edp .stat b{font-size:28px}
.edp table{width:100%;border-collapse:collapse}.edp th{text-align:left;font-size:12px;color:#64748b;text-transform:uppercase;padding:8px}
.edp td{padding:10px 8px;border-top:1px solid #f1f5f9}.edp tbody tr{cursor:pointer}.edp tbody tr:hover{background:#f8fafc}
.edp tr.sel{background:#eff6ff!important}
.edp .badge{color:#fff;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600}
.edp .muted{color:#64748b;font-size:14px}.edp .meta p{margin:6px 0;font-size:14px}
.edp .ov{position:fixed;inset:0;background:rgba(15,23,42,.5);display:flex;justify-content:center;align-items:center}
.edp .modal{width:440px;background:#fff;border-radius:12px;padding:22px;display:grid;gap:10px}
.edp .modal h3{margin:0}.edp .lbl{font-size:12px;color:#64748b}
.edp .err{color:#ef4444;font-size:13px}
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

export default function EmailDiscoveryPortal({ workItem }: { workItem: EmailDiscoveryWorkItem }) {
  const [searchText, setSearchText] = useState('');
  const [query, setQuery] = useState('');
  const [adv, setAdv] = useState<AdvFilters>(EMPTY_ADV);
  const [draft, setDraft] = useState<AdvFilters>(EMPTY_ADV);
  const [feeds, setFeeds] = useState<string[]>(FEEDS);
  const [selMailboxes, setSelMailboxes] = useState<string[]>(MAILBOXES);
  const [selSources, setSelSources] = useState<string[]>(FEEDS);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [modal, setModal] = useState<'adv' | 'feed' | null>(null);
  const [newFeed, setNewFeed] = useState('');
  const emailsForWork = useMemo<MailEmail[]>(() => {
    const appointmentWork = workItem.work_item_id === 'role01-work-1';
    return [{
      id: 1,
      code: workItem.customer_request_id,
      scenario: 'Current Work Item',
      subject: appointmentWork ? 'Customer appointment inquiry' : workItem.work_item,
      from: appointmentWork ? 'ram@local.dev' : 'customer@local.dev',
      mailbox: 'HP Mailbox',
      source: 'Exchange',
      sensitivity: 'Medium',
      date: '2026-10-07',
      attachment: '',
      content: appointmentWork
        ? 'Ram contacted Swati to discuss the customer appointment and confirm the requested time of 11:30 AM on 8 November.'
        : `Demo email context for ${workItem.label}: ${workItem.work_item}. Request ${workItem.customer_request_id}.`,
    }, ...SCENARIO_EMAILS];
  }, [workItem]);

  const emails = useMemo(
    () =>
      emailsForWork.filter(
        (m) =>
          selMailboxes.includes(m.mailbox) &&
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
    [emailsForWork, selMailboxes, selSources, query, adv]
  );
  const selected = emails.find((m) => m.id === selectedId);
  const advActive = JSON.stringify(adv) !== JSON.stringify(EMPTY_ADV);

  const search = () => {
    setQuery(searchText.trim());
    setSelectedId(null);
  };
  const reset = () => {
    setSearchText(''); setQuery(''); setAdv(EMPTY_ADV); setDraft(EMPTY_ADV);
    setSelMailboxes(MAILBOXES); setSelSources(feeds); setSelectedId(null);
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
    <div className="edp">
      <style>{CSS}</style>

      <header className="hdr">
        <h2>Email Discovery Portal</h2>
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
          <div className="grp"><CheckList title="📬 Mailboxes" items={MAILBOXES} sel={selMailboxes} setSel={setSelMailboxes} /></div>
          <hr style={{ border: 0, borderTop: '1px solid #e2e8f0', margin: '16px 0' }} />
          <div className="grp"><CheckList title="🔗 Sources" items={feeds} sel={selSources} setSel={setSelSources} onRemove={removeFeed} /></div>
          <button className="btn pri" style={{ width: '100%', marginTop: 16 }} onClick={() => setModal('feed')}>+ Add Feed</button>
        </aside>

        <main>
          <div className="stats">
            <div className="stat" style={{ background: '#2563eb' }}><p>Total Emails</p><b>{emails.length}</b></div>
            <div className="stat" style={{ background: '#ef4444' }}><p>High Sensitivity</p><b>{emails.filter((e) => e.sensitivity === 'High').length}</b></div>
            <div className="stat" style={{ background: '#10b981' }}><p>Active Sources</p><b>{selSources.length}</b></div>
          </div>
          <div className="card">
            <h3>📋 Search Results</h3>
            {emails.length ? (
              <table>
                <thead><tr><th>ID</th><th>Scenario</th><th>Subject</th><th>Mailbox</th><th>Date</th><th>Sensitivity</th></tr></thead>
                <tbody>
                  {emails.map((m) => (
                    <tr key={m.id} className={m.id === selectedId ? 'sel' : ''} onClick={() => setSelectedId(m.id)}>
                      <td>{m.code}</td><td>{m.scenario}</td><td>{m.subject}</td><td>{m.mailbox}</td><td>{m.date}</td>
                      <td><span className="badge" style={{ background: BADGE[m.sensitivity] }}>{m.sensitivity}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="muted">No emails match your filters. <button className="link" onClick={reset}>Clear all filters</button></p>
            )}
          </div>
        </main>

        <section className="card">
          <h3>📩 Email Preview</h3>
          {selected ? (
            <div className="meta">
              <h2 style={{ margin: '0 0 10px' }}>{selected.subject}</h2>
              <p><b>ID:</b> {selected.code}</p>
              <p><b>Scenario:</b> {selected.scenario}</p>
              <p><b>From:</b> {selected.from}</p>
              <p><b>Mailbox:</b> {selected.mailbox}</p>
              <p><b>Source:</b> {selected.source}</p>
              <p><b>Date:</b> {selected.date}</p>
              <p><b>Sensitivity:</b> <span className="badge" style={{ background: BADGE[selected.sensitivity] }}>{selected.sensitivity}</span></p>
              <hr /><p>{selected.content}</p><hr />
              {selected.attachment && <p>📎 {selected.attachment}</p>}
            </div>
          ) : (
            <p className="muted">Select an email from search results.</p>
          )}
        </section>
      </div>

      {modal === 'adv' && (
        <div className="ov" onClick={() => setModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Advanced Search</h3>
            <input className="inp" placeholder="Subject" value={draft.subject} onChange={setD('subject')} />
            <input className="inp" placeholder="Sender email" value={draft.sender} onChange={setD('sender')} />
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
