import { FormEvent, useEffect, useRef, useState } from 'react';

type Product = { id: number; name: string; product_name?: string; category: string | null; location: string | null; completion_date: string; overall_condition: number | null; is_intact: boolean | null; is_clean: boolean | null; quantity: number; additional_notes: string | null; process: string | null; process_id: string | null; material: string | null; material_id: number | null; material_category: string | null; material_verification: string | null; material_confidence: number | null; ai_status: string; assessment_status: string; field_provenance?: Record<string, string>; field_verification?: Record<string, string> };
type ProcessOption = { process: string; process_id: string };
type CanonicalMaterial = { material: string; material_id: number; material_category: string };
type MaterialSuggestion = { suggested_name: string | null; material: string | null; material_id: number | null; material_category: string | null; confidence: number; match_score: number; candidate_count: number; status: 'suggested' | 'uncertain' | 'unresolved' | 'unknown' };
type ImageRow = { id: number; filename: string; content_type: string; is_primary: boolean; url: string };
type Material = { id?: number; name: string; percentage: number | null; verification: string };
type Row = { product: Product; materials: Material[]; images: ImageRow[] };
type FormValues = { name: string; category: string; process: string; location: string; overall_condition: string; is_intact: string; is_clean: string; quantity: string; additional_notes: string; material: string };
type InventoryDraft = Pick<FormValues, 'name' | 'category' | 'process' | 'location' | 'overall_condition' | 'is_intact' | 'is_clean' | 'quantity' | 'additional_notes' | 'material'>;
const API = import.meta.env.VITE_API_URL || '/api';
type AuthUser = { id: number; username: string; is_active: boolean; created_at: string };
let csrfToken = '';
let onAuthenticationExpired = () => {};

async function apiFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  const method = (init.method || 'GET').toUpperCase();
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method) && csrfToken) headers.set('X-CSRF-Token', csrfToken);
  const response = await window.fetch(input, { ...init, headers, credentials: 'include' });
  const url = new URL(typeof input === 'string' ? input : input instanceof URL ? input.href : input.url, window.location.href);
  if (response.status === 401 && !url.pathname.endsWith('/auth/login') && !url.pathname.endsWith('/auth/me')) {
    csrfToken = '';
    onAuthenticationExpired();
  }
  return response;
}

function LoginPage({ onLogin }: { onLogin: (username: string, password: string) => Promise<string | null> }) {
  const [username, setUsername] = useState(''), [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('');
  async function submit(event: FormEvent) {
    event.preventDefault(); setError('');
    if (!username.trim() || password.length < 5) { setError('Enter a username and a password of at least 5 characters.'); return; }
    setBusy(true);
    try { const message = await onLogin(username, password); if (message) setError(message); }
    catch { setError('Could not reach RAKKI. Check the server and try again.'); }
    finally { setBusy(false); }
  }
  return <main className="login-shell"><form className="login-card" onSubmit={submit}>
    <div className="brand">RAKKI<span> / PRODUCT INTELLIGENCE</span></div>
    <p className="eyebrow">SECURE WORKSPACE</p><h1>Welcome back.</h1><p className="login-copy">Sign in to access your product workspace.</p>
    <label className="login-field">Username<input autoComplete="username" value={username} onChange={event => setUsername(event.target.value)} maxLength={80} required autoFocus/></label>
    <label className="login-field">Password<span className="password-input"><input type={showPassword ? 'text' : 'password'} autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} minLength={5} maxLength={256} required/><button type="button" className="password-toggle" onClick={() => setShowPassword(value => !value)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? 'Hide' : 'Show'}</button></span></label>
    {error && <p className="notice error-notice" role="alert">{error}</p>}
    <button className="login-submit" disabled={busy || !username.trim() || password.length < 5}>{busy ? 'Signing in…' : 'Sign in →'}</button>
  </form></main>;
}
const LOCATION_OPTIONS = [ 'Office building, health center',  'Commercial building',  'Accommodation building',  'Education building, daycare centre',  'Apartment building',  'Small apartment building',  'Building for sports and physical exercise',  'Hospital',  'Other building, warehouse',  'Other building, indoor ice rink',  'Other building, transport and communications building',  'Other building, indoor swimming pool','others'];
const CATEGORY_OPTIONS = ['Movable Furniture and Fixed Furnishings', 'Electrical', 'HVAC and Plumbing', 'Building Components and Materials', 'Other'];
const CONDITION_OPTIONS = [{ value: '', label: 'Not Assessed' }, { value: '1', label: '1 - Very Poor' }, { value: '2', label: '2 - Poor' }, { value: '3', label: '3 - Fair' }, { value: '4', label: '4 - Good' }, { value: '5', label: '5 - Excellent' }];
const ASSESSMENT_OPTIONS = [{ value: '', label: 'Not Assessed' }, { value: 'true', label: 'Yes' }, { value: 'false', label: 'No' }];
const emptyForm = (): FormValues => ({ name: '', category: '', process: '', location: '', overall_condition: '', is_intact: 'true', is_clean: 'true', quantity: '1', additional_notes: '', material: '' });
const fields: { key: keyof FormValues; label: string }[] = [
  { key: 'name', label: 'Product name' }, { key: 'category', label: 'Category' }, { key: 'process', label: 'Process' },
  { key: 'location', label: 'Location' }, { key: 'overall_condition', label: 'Overall condition' }, { key: 'is_intact', label: 'Product is intact' },
  { key: 'is_clean', label: 'Product is clean' }, { key: 'quantity', label: 'Quantity' },

];
function errorText(data: any, fallback: string) {
  const detail = data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.errors) return detail.errors.join('; ');
  if (Array.isArray(detail)) return detail.map((item: any) => `${item.loc?.slice(-1)[0] || 'Field'}: ${item.msg}`).join('; ');
  if (detail?.message) return detail.message;
  return fallback;
}
const emptyInventoryDraft = (): InventoryDraft => ({ name: '', category: '', process: '', location: '', overall_condition: '', is_intact: 'true', is_clean: 'true', quantity: '1', additional_notes: '', material: '' });
const positiveInteger = (value: string) => /^\d+$/.test(value) && Number(value) > 0;
const boolValue = (value: string): boolean | null => value === 'true' ? true : value === 'false' ? false : null;
const conditionLabel = (value: number | null) => CONDITION_OPTIONS.find(option => option.value === String(value ?? ''))?.label || 'Not Assessed';
const assessedLabel = (value: boolean | null) => value === true ? 'Yes' : value === false ? 'No' : 'Not Assessed';
const displayDate = (value: string) => {
  const [year, month, day] = value.split('-');
  return year && month && day ? `${day}.${month}.${year}` : value;
};
const materialKey = (value: string) => value.trim().replace(/\s+/g, ' ').toLocaleLowerCase();
function inventoryPayload(draft: InventoryDraft) {
  return {
    name: draft.name.trim(), category: draft.category || null, location: draft.location.trim() || null,
    overall_condition: draft.overall_condition ? Number(draft.overall_condition) : null,
    is_intact: boolValue(draft.is_intact), is_clean: boolValue(draft.is_clean), quantity: Number(draft.quantity),
    additional_notes: draft.additional_notes.trim() || null, material: draft.material.trim() || null, process: draft.process || 'Others',
  };
}

function Workspace({ onLogout }: { onLogout: () => void }) {
  const [rows, setRows] = useState<Row[]>([]), [q, setQ] = useState(''), [status, setStatus] = useState('');
  const [tab, setTab] = useState<'catalog' | 'inventory'>('catalog'), [page, setPage] = useState(0), [totalCount, setTotalCount] = useState(0), [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<Row | null>(null), [form, setForm] = useState<FormValues>(emptyForm());
  const [materialOptions, setMaterialOptions] = useState<CanonicalMaterial[]>([]), [processOptions, setProcessOptions] = useState<ProcessOption[]>([]), [materialSuggestion, setMaterialSuggestion] = useState<MaterialSuggestion | null>(null);
  const [createDraft, setCreateDraft] = useState<InventoryDraft>(emptyInventoryDraft()), [createFiles, setCreateFiles] = useState<File[]>([]);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]), [analysisImage, setAnalysisImage] = useState<number | ''>('');
  const [createPreviews, setCreatePreviews] = useState<string[]>([]), [pendingPreviews, setPendingPreviews] = useState<string[]>([]);
  const [busy, setBusy] = useState(false), [analysisBusy, setAnalysisBusy] = useState(false), [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(''), [error, setError] = useState('');
  const [inventoryAdding, setInventoryAdding] = useState(false), [inventoryEditingId, setInventoryEditingId] = useState<number | null>(null), [inventoryDraft, setInventoryDraft] = useState<InventoryDraft>(emptyInventoryDraft()), [inventorySaving, setInventorySaving] = useState(false);
  const [suggested, setSuggested] = useState<Set<keyof FormValues>>(new Set());
  const formRef = useRef(form), touchedRef = useRef(new Set<keyof FormValues>());
  const createCameraRef = useRef<HTMLInputElement>(null), pendingCameraRef = useRef<HTMLInputElement>(null);
  const uploadLockRef = useRef(false);
  function processId(value: string) { return processOptions.find(option => option.process === value)?.process_id; }
  function canonicalMaterial(value: string) { return materialOptions.find(option => materialKey(option.material) === materialKey(value)); }

  async function load() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (q) params.set('q', q);
      if (status) params.set('status', status);
      params.set('limit', '50'); params.set('offset', String(page * 50));
      const response = await apiFetch(`${API}/products?${params}`);
      if (!response.ok) throw new Error('API unavailable; start the backend and configure MySQL.');
      setRows(await response.json()); setTotalCount(Number(response.headers.get('X-Total-Count') || '0')); setError('');
    } catch (err) { setError(String(err)); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, [q, status, page]);
  useEffect(() => {
    apiFetch(`${API}/processes`).then(response => response.json()).then(setProcessOptions).catch(err => setError(String(err)));
    apiFetch(`${API}/materials`).then(response => {
      if (!response.ok) throw new Error('Could not load canonical materials');
      return response.json();
    }).then(setMaterialOptions).catch(err => setError(String(err)));
  }, []);
  console.log("RAKKI component rendered");
  useEffect(() => {
    // const urls = createFiles.map(file => URL.createObjectURL(file)); setCreatePreviews(urls);
    const urls = createFiles.map((file, index) => {
      console.log("Image index:", index);
      console.log("File value:", file);
      console.log("Is File:", file instanceof File);
      console.log("Is Blob:", file instanceof Blob);

      return URL.createObjectURL(file);
    });
    return () => urls.forEach(url => URL.revokeObjectURL(url));
  }, [createFiles]);
  useEffect(() => {
    const urls = pendingFiles.map(file => URL.createObjectURL(file)); setPendingPreviews(urls);
    return () => urls.forEach(url => URL.revokeObjectURL(url));
  }, [pendingFiles]);
  async function loadDetail(id: number) {
    const response = await apiFetch(`${API}/products/${id}`);
    if (!response.ok) throw new Error('Could not load product details');
    const detail: Row = await response.json();
    const values: FormValues = {
      name: detail.product.name || '', category: detail.product.category || '', process: detail.product.process || '', location: detail.product.location || '',
      overall_condition: detail.product.overall_condition == null ? '' : String(detail.product.overall_condition),
      is_intact: detail.product.is_intact == null ? '' : String(detail.product.is_intact),
      is_clean: detail.product.is_clean == null ? '' : String(detail.product.is_clean),
      quantity: String(detail.product.quantity ?? 1), additional_notes: detail.product.additional_notes || '',
      material: detail.product.material || '',
    };
    const cleanTouched = new Set<keyof FormValues>();
    setSelected(detail); formRef.current = values; setForm(values); setMaterialSuggestion(null);
    touchedRef.current = cleanTouched; setSuggested(new Set()); setAnalysisImage(detail.images.find(i => i.is_primary)?.id ?? detail.images[0]?.id ?? '');
  }
  function applySuggestions(data: Record<string, unknown>) {
    const current = formRef.current;
    const next = { ...current };
    const newlySuggested = new Set<keyof FormValues>();
    for (const { key } of fields) {
      const value = data[key];
      const previouslyVerified = selected?.product.field_verification?.[key] === 'verified';
      if (typeof value === 'string' && !previouslyVerified && !touchedRef.current.has(key) && !String(current[key] || '').trim() && value.trim()) {
        next[key] = value; newlySuggested.add(key);
      }
    }
    formRef.current = next; setForm(next); setSuggested(newlySuggested);
    setMessage('AI suggestions added to blank fields. Review and save them to update the product. Suggestions are unverified.');
  }
  async function analyze(id: number, imageId?: number) {
    setAnalysisBusy(true); setError(''); setMessage('Analyzing image…');
    try {
      const suffix = imageId ? `?image_id=${imageId}` : '';
      const current = formRef.current;
      const context = { product_name: current.name, category: current.category, location: current.location, additional_notes: current.additional_notes };
      const response = await apiFetch(`${API}/products/${id}/analyze${suffix}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(context) });
      const result = await response.json();
      if (!response.ok) throw new Error(errorText(result, 'Image analysis failed. Your image and product data are still saved.'));
      applySuggestions({ name: result.data?.product_name, category: result.data?.category, process: result.data?.process_suggestion?.process });
      if (result.data?.material_suggestion?.material) { const next = { ...formRef.current, material: result.data.material_suggestion.material }; formRef.current = next; setForm(next); setSuggested(current => new Set(current).add('material')); }
      const material = result.data?.material_suggestion as MaterialSuggestion | undefined;
      if (material) {
        setMaterialSuggestion(material);
        if (material.material && (!formRef.current.material || suggested.has('material')) && !touchedRef.current.has('material') && selected?.product.material_verification !== 'verified') {
          const next = { ...formRef.current, material: material.material };
          formRef.current = next; setForm(next); setSuggested(current => new Set(current).add('material'));
        }
        if (material.status === 'unresolved') setMessage('Gemini returned a material name that is not an exact canonical match. Choose a material from the list to continue.');
        else if (material.status === 'unknown') setMessage('Gemini could not identify a material reliably. Choose one from the canonical list if you can confirm it.');
        else setMessage(`Gemini suggested ${material.material}${material.status === 'uncertain' ? ' with uncertainty' : ''}. Review or change it before saving.`);
      }
      setSelected(current => current ? { ...current, product: { ...current.product, ai_status: 'completed' } } : current);
      await load();
    } catch (err) { setError(`${String(err)} The uploaded image and entered information are preserved. You can retry analysis.`); setMessage(''); }
    finally { setAnalysisBusy(false); }
  }
  async function uploadFiles(id: number, files: File[]) {
    if (!files.length) return [] as ImageRow[];
    if (uploadLockRef.current) throw new Error('An image upload is already in progress.');
    uploadLockRef.current = true;
    try {
      const body = new FormData(); files.forEach(item => body.append('files', item));
      const response = await apiFetch(`${API}/products/${id}/images`, { method: 'POST', body });
      const result = await response.json();
      if (!response.ok) throw new Error(errorText(result, 'Image upload failed'));
      if (result.errors?.length) setError(`Some images could not be uploaded: ${result.errors.join('; ')}`);
      return result.uploaded as ImageRow[];
    } finally { uploadLockRef.current = false; }
  }
  async function create(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(''); setMessage('');
    try {
      if (!positiveInteger(createDraft.quantity)) throw new Error('Quantity must be a positive whole number.');
      const response = await apiFetch(`${API}/products`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(inventoryPayload(createDraft)) });
      const product = await response.json();
      if (!response.ok) throw new Error(errorText(product, 'Could not create product'));
      setCreateDraft(emptyInventoryDraft()); setCreateFiles([]);
      let uploaded: ImageRow[] = [];
      if (createFiles.length) uploaded = await uploadFiles(product.id, createFiles);
      await loadDetail(product.id); await load();
      if (uploaded.length) await analyze(product.id, uploaded[0].id);
    } catch (err) { setError(String(err)); await load(); }
    finally { setBusy(false); }
  }
  async function save(event: FormEvent) {
    event.preventDefault(); if (!selected) return;
    setSaving(true); setError(''); setMessage('');
    try {
      if (!positiveInteger(form.quantity)) throw new Error('Quantity must be a positive whole number.');
      const payload = { ...inventoryPayload(form), material: form.material.trim() || null };
      if (form.material && !canonicalMaterial(form.material)) throw new Error('Choose a material from the canonical list.');
      const response = await apiFetch(`${API}/products/${selected.product.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const result = await response.json();
      if (!response.ok) throw new Error(errorText(result, 'Could not save product changes'));
      await loadDetail(selected.product.id); await load(); setSuggested(new Set()); setMaterialSuggestion(null); setMessage('Product changes saved. The selected material and its mapped ID and category were confirmed.');
    } catch (err) { setError(String(err)); }
    finally { setSaving(false); }
  }
  async function addImages() {
    if (!selected || !pendingFiles.length) return;
    setBusy(true); setError('');
    try {
      const added = await uploadFiles(selected.product.id, pendingFiles);
      setPendingFiles([]); await loadDetail(selected.product.id); await load();
      if (added.length) await analyze(selected.product.id, added[0].id);
    } catch (err) { setError(String(err)); }
    finally { setBusy(false); }
  }
  async function choosePrimary(image: ImageRow) {
    if (!selected) return;
    const response = await apiFetch(`${API}/products/${selected.product.id}/images/${image.id}/primary`, { method: 'POST' });
    if (!response.ok) { setError('Could not select the primary image'); return; }
    await loadDetail(selected.product.id); await load();
  }
  async function removeImage(image: ImageRow) {
    if (!selected || !window.confirm('Remove this image from the product?')) return;
    const response = await apiFetch(`${API}/products/${selected.product.id}/images/${image.id}`, { method: 'DELETE' });
    if (!response.ok) { setError('Could not delete image'); return; }
    await loadDetail(selected.product.id); await load();
  }
  async function removeProduct(product: Product) {
    if (!window.confirm(`Delete “${product.name}” and all its images, assessments, and revision history? This cannot be undone.`)) return;
    setBusy(true);
    try {
      const response = await apiFetch(`${API}/products/${product.id}`, { method: 'DELETE' });
      if (!response.ok) throw new Error(errorText(await response.json(), 'Could not delete product'));
      if (selected?.product.id === product.id) setSelected(null);
      setMessage('Product deleted.'); await load();
    } catch (err) { setError(String(err)); }
    finally { setBusy(false); }
  }
  function editInventory(row: Row) {
    const product = row.product;
    setInventoryDraft({ name: product.name || '', category: product.category || '', process: product.process || '', location: product.location || '', material: product.material || '',
      overall_condition: product.overall_condition == null ? '' : String(product.overall_condition),
      is_intact: product.is_intact == null ? '' : String(product.is_intact), is_clean: product.is_clean == null ? '' : String(product.is_clean),
      quantity: String(product.quantity ?? 1), additional_notes: product.additional_notes || '' });
    setInventoryAdding(false); setInventoryEditingId(product.id);
  }
  async function saveInventory() {
    if (!positiveInteger(inventoryDraft.quantity)) { setError('Quantity must be a positive whole number.'); return; }
    if (inventoryDraft.material && !canonicalMaterial(inventoryDraft.material)) { setError('Choose a material from the canonical list.'); return; }
    setInventorySaving(true); setError(''); setMessage('');
    try {
      const url = inventoryAdding ? `${API}/products` : `${API}/products/${inventoryEditingId}`;
      const response = await apiFetch(url, { method: inventoryAdding ? 'POST' : 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(inventoryPayload(inventoryDraft)) });
      const result = await response.json();
      if (!response.ok) throw new Error(errorText(result, 'Could not save inventory item'));
      setInventoryAdding(false); setInventoryEditingId(null); setMessage(inventoryAdding ? 'Inventory item created.' : 'Inventory item updated.'); await load();
    } catch (err) { setError(String(err)); }
    finally { setInventorySaving(false); }
  }
  function cancelInventoryEdit() { setInventoryAdding(false); setInventoryEditingId(null); setInventoryDraft(emptyInventoryDraft()); }
  function updateCreateDraft(key: keyof InventoryDraft, value: string) { setCreateDraft(current => ({ ...current, [key]: value })); }
  function updateField(key: keyof FormValues, value: string) {
    touchedRef.current = new Set(touchedRef.current).add(key);
    setSuggested(current => { const next = new Set(current); next.delete(key); return next; });
    if (key === 'material') setMaterialSuggestion(null);
    const nextForm = { ...formRef.current, [key]: value }; formRef.current = nextForm; setForm(nextForm);
  }
  function filePicker(files: FileList | null, setter: (value: File[]) => void) { setter(Array.from(files || [])); }
  function editInput(key: keyof FormValues) {
    const onChange = (value: string) => updateField(key, value);
    if (key === 'location') return (    <select      value={form.location}      onChange={e => onChange(e.target.value)}    >      <option value="">Choose location</option>      {LOCATION_OPTIONS.map(option => (        <option key={option} value={option}>          {option}        </option>      ))}    </select>);
    if (key === 'process') return <select value={form.process} onChange={e => onChange(e.target.value)}><option value="">Choose process</option>{processOptions.map(option => <option key={option.process} value={option.process}>{option.process}</option>)}</select>;
    if (key === 'category') return <select value={form.category} onChange={e => onChange(e.target.value)}><option value="">Choose category</option>{form.category && !CATEGORY_OPTIONS.includes(form.category) && <option value={form.category}>{form.category} (legacy)</option>}{CATEGORY_OPTIONS.map(option => <option key={option}>{option}</option>)}</select>;
    if (key === 'overall_condition') return <select value={form.overall_condition} onChange={e => onChange(e.target.value)}>{CONDITION_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select>;
    if (key === 'is_intact' || key === 'is_clean') return <select value={form[key]} onChange={e => onChange(e.target.value)}>{ASSESSMENT_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select>;
    if (key === 'quantity') return <input type="number" min="1" step="1" value={form.quantity} onChange={e => onChange(e.target.value)}/>;
    if (key === 'additional_notes') return <textarea value={form[key] || ''} onChange={e => onChange(e.target.value)} rows={3}/>;
    return <input value={form[key] || ''} onChange={e => onChange(e.target.value)}/>;
  }

  return <main>
    <datalist id="process-options">{processOptions.map(option => <option key={option.process} value={option.process}/>)}</datalist>
    <datalist id="material-options">{materialOptions.map(option => <option key={option.material} value={option.material}/>)}</datalist>
    <header><div className="brand">RAKKI<span> / PRODUCT INTELLIGENCE</span></div><nav className="tabs"><button className={tab === 'catalog' ? 'active' : ''} onClick={() => setTab('catalog')}>Catalog</button><button className={tab === 'inventory' ? 'active' : ''} onClick={() => setTab('inventory')}>Inventory</button></nav><a href={`${API}/export.xlsx`}>Export Excel ↓</a><button className="secondary logout-button" onClick={onLogout}>Log out</button></header>
    {error && <p className="notice error-notice">{error}</p>}{message && <p className="notice">{message}</p>}
    {tab === 'catalog' && <>
      <section className="intro"><p className="eyebrow">MATERIALS · EVIDENCE · IMPACT</p><h1>Know what your<br/><i>products are made of.</i></h1><p className="sub">A product assessment workspace with transparent evidence and careful AI assistance.</p></section>
      <form className="create inventory-create" onSubmit={create}>
        <div className="create-fields">
          <label className="field"><span>Location</span><select value={createDraft.location} onChange={e => updateCreateDraft('location', e.target.value)}><option value="">Choose location</option>{LOCATION_OPTIONS.map(option => <option key={option}>{option}</option>)}</select></label>
          <label className="field"><span>Category</span><select value={createDraft.category} onChange={e => updateCreateDraft('category', e.target.value)}><option value="">Choose category</option>{CATEGORY_OPTIONS.map(option => <option key={option}>{option}</option>)}</select></label>
          <label className="field"><span>Overall condition</span><select value={createDraft.overall_condition} onChange={e => updateCreateDraft('overall_condition', e.target.value)}>{CONDITION_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
          <label className="field"><span>Product is intact</span><select value={createDraft.is_intact} onChange={e => updateCreateDraft('is_intact', e.target.value)}>{ASSESSMENT_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
          <label className="field"><span>Product is clean</span><select value={createDraft.is_clean} onChange={e => updateCreateDraft('is_clean', e.target.value)}>{ASSESSMENT_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
          <label className="field"><span>Quantity</span><input type="number" min="1" step="1" value={createDraft.quantity} onChange={e => updateCreateDraft('quantity', e.target.value)} required/></label>
          <label className="field"><span>Process</span><select value={createDraft.process} onChange={e => updateCreateDraft('process', e.target.value)}><option value="">AI will suggest after image upload</option>{processOptions.map(option => <option key={option.process}>{option.process}</option>)}</select></label>
          <label className="field"><span>Process ID</span><input readOnly value={processId(createDraft.process) || ''}/></label>
          <label className="field"><span>Material</span><input list="material-options" value={createDraft.material} onChange={e => { const value = e.target.value; updateCreateDraft('material', canonicalMaterial(value)?.material || value); }} placeholder="Search canonical materials"/></label>
          <label className="field"><span>Material ID</span><input readOnly value={canonicalMaterial(createDraft.material)?.material_id ?? ''}/></label>
          <label className="field"><span>Material Category</span><input readOnly value={canonicalMaterial(createDraft.material)?.material_category ?? ''}/></label>
          <label className="field notes-field"><span>Additional notes</span><textarea rows={2} value={createDraft.additional_notes} onChange={e => updateCreateDraft('additional_notes', e.target.value)} placeholder="Dimensions, visible damage, accessories…"/></label>
          <label className="file-label">Upload a Picture<input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={e => filePicker(e.target.files, setCreateFiles)}/></label>
          <button type="button" className="secondary camera-button" onClick={() => createCameraRef.current?.click()} disabled={busy}>Take a Picture</button>
          <input ref={createCameraRef} className="camera-input" type="file" accept="image/*" capture="environment" onChange={e => { if (e.target.files?.[0]) setCreateFiles(current => [...current, e.target.files![0]]); e.target.value = ''; }}/>
          {createFiles.length > 0 && <small>{createFiles.length} image(s) selected. Review, remove or retake before creating the product.</small>}
          <div className="preview-strip">{createPreviews.map((url, index) => <div className="image-preview" key={url}><img src={url} alt={`Selected upload ${index + 1}`}/><button type="button" className="secondary" onClick={() => setCreateFiles(current => current.filter((_, itemIndex) => itemIndex !== index))}>Remove / retake</button></div>)}</div>
        </div>
        <button disabled={busy || !positiveInteger(createDraft.quantity)}>{busy ? 'Working…' : 'Create product →'}</button>
      </form>
      <section className="listHead"><div><label>YOUR CATALOG</label><h2>Products <small>{totalCount.toString().padStart(2, '0')}</small></h2></div><div className="filters"><select value={status} onChange={e => { setStatus(e.target.value); setPage(0); }} aria-label="Filter by assessment status"><option value="">All statuses</option><option value="incomplete">Incomplete</option><option value="complete">Complete</option></select><input className="search" value={q} onChange={e => { setQ(e.target.value); setPage(0); }} placeholder="Search name or process…"/></div></section>
      <div className="grid">{rows.map(row => { const primary = row.images.find(image => image.is_primary) || row.images[0]; return <article className="product-card" key={row.product.id}>
        <button className="card-open" onClick={() => { void loadDetail(row.product.id).catch(err => setError(String(err))); }} aria-label={`Open ${row.product.name || 'unnamed product'}`}>
          <div className="tile">{primary ? <img src={primary.url} alt={row.product.name || 'Product image'}/> : <div className="placeholder"><span>NO PRODUCT IMAGE</span><b>RAKKI</b></div>}<span className="category-tag">{row.product.category || 'PRODUCT'}</span><strong>{row.product.name || 'Unnamed product'}</strong></div>
          <div className="row"><span>{row.product.process || 'Process not recorded'}</span><span className="pill">{row.product.assessment_status}</span></div>
        </button><button className="card-delete" onClick={() => void removeProduct(row.product)} disabled={busy}>Delete</button>
      </article>; })}</div>
      {loading && <p className="empty">Loading products…</p>}{rows.length === 0 && !loading && !error && <p className="empty">Your catalog is ready. Add a product to begin.</p>}
      <div className="pagination"><button className="secondary" disabled={page === 0 || loading} onClick={() => setPage(value => Math.max(0, value - 1))}>Previous</button><span>Page {page + 1} of {Math.max(1, Math.ceil(totalCount / 50))}</span><button className="secondary" disabled={(page + 1) * 50 >= totalCount || loading} onClick={() => setPage(value => value + 1)}>Next</button></div>
    </>}
    {tab === 'inventory' && <section className="inventory-view">
      <div className="listHead"><div><label>PRODUCT RECORDS</label><h2>Inventory <small>{totalCount.toString().padStart(2, '0')}</small></h2></div><div className="inventory-actions"><div className="filters"><select value={status} onChange={e => { setStatus(e.target.value); setPage(0); }} aria-label="Filter by assessment status"><option value="">All statuses</option><option value="incomplete">Incomplete</option><option value="complete">Complete</option></select><input className="search" value={q} onChange={e => { setQ(e.target.value); setPage(0); }} placeholder="Search products…"/></div><button disabled={inventoryAdding || inventoryEditingId !== null} onClick={() => { setInventoryAdding(true); setInventoryDraft(emptyInventoryDraft()); }}>Add item</button></div></div>
      {loading && <p className="empty">Loading inventory…</p>}
      <div className="table-scroll"><table className="inventory-table"><thead><tr><th>ID</th><th>Completion Date</th><th>Location</th><th>Category</th><th>Process</th><th>Process ID</th><th>Material</th><th>Material ID</th><th>Material Category</th><th>Product Name</th><th>Overall Condition</th><th>Product Is Intact</th><th>Product Is Clean</th><th>Quantity</th><th>Additional Notes</th><th>Actions</th></tr></thead><tbody>
        {inventoryAdding && <tr className="editing-row"><td>—</td><td>—</td><td>  <select    value={inventoryDraft.location}    onChange={e =>      setInventoryDraft(d => ({        ...d,        location: e.target.value      }))    }  >    <option value="">Choose location</option>    {LOCATION_OPTIONS.map(option => (      <option key={option} value={option}>        {option}      </option>    ))}  </select></td><td><select value={inventoryDraft.category} onChange={e => setInventoryDraft(d => ({ ...d, category: e.target.value }))}><option value="">Choose</option>{CATEGORY_OPTIONS.map(option => <option key={option}>{option}</option>)}</select></td><td><select value={inventoryDraft.process} onChange={e => setInventoryDraft(d => ({ ...d, process: e.target.value }))}><option value="">Choose process</option>{processOptions.map(option => <option key={option.process}>{option.process}</option>)}</select></td><td>{processId(inventoryDraft.process) || '—'}</td><td><input list="material-options" value={inventoryDraft.material} onChange={e => { const value = e.target.value; setInventoryDraft(d => ({ ...d, material: canonicalMaterial(value)?.material || value })); }}/></td><td>{canonicalMaterial(inventoryDraft.material)?.material_id ?? '—'}</td><td>{canonicalMaterial(inventoryDraft.material)?.material_category ?? '—'}</td><td>—</td><td><select value={inventoryDraft.overall_condition} onChange={e => setInventoryDraft(d => ({ ...d, overall_condition: e.target.value }))}>{CONDITION_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></td><td><select value={inventoryDraft.is_intact} onChange={e => setInventoryDraft(d => ({ ...d, is_intact: e.target.value }))}>{ASSESSMENT_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></td><td><select value={inventoryDraft.is_clean} onChange={e => setInventoryDraft(d => ({ ...d, is_clean: e.target.value }))}>{ASSESSMENT_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></td><td><input type="number" min="1" step="1" value={inventoryDraft.quantity} onChange={e => setInventoryDraft(d => ({ ...d, quantity: e.target.value }))}/></td><td><textarea value={inventoryDraft.additional_notes} onChange={e => setInventoryDraft(d => ({ ...d, additional_notes: e.target.value }))} rows={2}/></td><td className="actions-cell"><button disabled={inventorySaving || !positiveInteger(inventoryDraft.quantity)} onClick={() => void saveInventory()}>Save</button><button className="secondary" disabled={inventorySaving} onClick={cancelInventoryEdit}>Cancel</button></td></tr>}
        {rows.map(row => {
          const editing = inventoryEditingId === row.product.id;
          const draft = editing ? inventoryDraft : null;
          return <tr key={row.product.id} className={editing ? 'editing-row' : ''}>
            <td>{row.product.id}</td><td>{displayDate(row.product.completion_date)}</td>
            <td>{editing ? <input value={draft!.location} onChange={e => setInventoryDraft(d => ({ ...d, location: e.target.value }))}/> : row.product.location || '—'}</td>
            <td>{editing ? <select value={draft!.category} onChange={e => setInventoryDraft(d => ({ ...d, category: e.target.value }))}><option value="">Choose</option>{draft!.category && !CATEGORY_OPTIONS.includes(draft!.category) && <option value={draft!.category}>{draft!.category} (legacy)</option>}{CATEGORY_OPTIONS.map(option => <option key={option}>{option}</option>)}</select> : row.product.category || '—'}</td>
            <td>{editing ? <select value={draft!.process} onChange={e => setInventoryDraft(d => ({ ...d, process: e.target.value }))}><option value="">Choose process</option>{processOptions.map(option => <option key={option.process}>{option.process}</option>)}</select> : row.product.process || '—'}</td><td>{editing ? processId(draft!.process) || '—' : row.product.process_id || '—'}</td>
            <td>{editing ? <input list="material-options" value={draft!.material} onChange={e => { const value = e.target.value; setInventoryDraft(d => ({ ...d, material: canonicalMaterial(value)?.material || value })); }} /> : row.product.material || '—'}</td>
            <td>{editing ? canonicalMaterial(draft!.material)?.material_id ?? '—' : row.product.material_id ?? '—'}</td>
            <td>{editing ? canonicalMaterial(draft!.material)?.material_category ?? '—' : row.product.material_category || '—'}</td>
            <td>{editing ? <input value={draft!.name} onChange={e => setInventoryDraft(d => ({ ...d, name: e.target.value }))} placeholder="Product name"/> : row.product.name || 'Unnamed product'}</td>
            <td>{editing ? <select value={draft!.overall_condition} onChange={e => setInventoryDraft(d => ({ ...d, overall_condition: e.target.value }))}>{CONDITION_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select> : conditionLabel(row.product.overall_condition)}</td>
            <td>{editing ? <select value={draft!.is_intact} onChange={e => setInventoryDraft(d => ({ ...d, is_intact: e.target.value }))}>{ASSESSMENT_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select> : assessedLabel(row.product.is_intact)}</td>
            <td>{editing ? <select value={draft!.is_clean} onChange={e => setInventoryDraft(d => ({ ...d, is_clean: e.target.value }))}>{ASSESSMENT_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select> : assessedLabel(row.product.is_clean)}</td>
            <td>{editing ? <input type="number" min="1" step="1" value={draft!.quantity} onChange={e => setInventoryDraft(d => ({ ...d, quantity: e.target.value }))}/> : row.product.quantity}</td>
            <td>{editing ? <textarea value={draft!.additional_notes} onChange={e => setInventoryDraft(d => ({ ...d, additional_notes: e.target.value }))} rows={2}/> : row.product.additional_notes || '—'}</td>
            <td className="actions-cell">{editing ? <><button disabled={inventorySaving || !positiveInteger(inventoryDraft.quantity)} onClick={() => void saveInventory()}>{inventorySaving ? 'Saving…' : 'Save'}</button><button className="secondary" disabled={inventorySaving} onClick={cancelInventoryEdit}>Cancel</button></> : <><button disabled={busy || inventoryAdding || inventoryEditingId !== null} onClick={() => editInventory(row)}>Edit</button><button className="danger" disabled={busy} onClick={() => void removeProduct(row.product)}>Delete</button></>}</td>
          </tr>;
        })}
        {!loading && rows.length === 0 && !inventoryAdding && <tr><td colSpan={16} className="table-empty">No inventory records yet.</td></tr>}
      </tbody></table></div>
      <div className="pagination"><button className="secondary" disabled={page === 0 || loading} onClick={() => setPage(value => Math.max(0, value - 1))}>Previous</button><span>Page {page + 1} of {Math.max(1, Math.ceil(totalCount / 50))}</span><button className="secondary" disabled={(page + 1) * 50 >= totalCount || loading} onClick={() => setPage(value => value + 1)}>Next</button></div>
    </section>}
    {selected && <div className="overlay" onClick={() => setSelected(null)}><section className="panel" onClick={e => e.stopPropagation()}>
      <button className="close" onClick={() => setSelected(null)} aria-label="Close">×</button><label>PRODUCT SHEET · #{selected.product.id}</label><h2>{selected.product.name || 'Unnamed product'}</h2>
      <p className="tag">AI status: {selected.product.ai_status} · AI suggestions are unverified until reviewed.</p>
      <form className="edit-form" onSubmit={save}><h3>Product information</h3>{fields.map(({ key, label }) => <label className="field" key={key}>{label}{suggested.has(key) ? <span className="suggestion-label">AI suggestion · unverified</span> : selected.product.field_verification?.[key] === 'verified' && <span className="verified-label">Manually reviewed</span>}{editInput(key)}</label>)}
        <label className="field notes-field"><span>Additional notes</span><textarea rows={3} value={form.additional_notes} onChange={e => updateField('additional_notes', e.target.value)}/></label>
        <label className="field"><span>Process ID</span><input readOnly value={processId(form.process) || (selected.product.process === form.process ? selected.product.process_id || '' : '')}/></label>
        <label className="field material-control"><span>Material</span>{materialSuggestion?.material && suggested.has('material') ? <span className="suggestion-label">Gemini suggestion · {materialSuggestion.status === 'uncertain' ? 'approximate / uncertain' : 'unverified'} · {Math.round(materialSuggestion.confidence * 100)}% confidence</span> : selected.product.material_verification === 'verified' && <span className="verified-label">User confirmed</span>}<input list="material-options" value={form.material} onChange={e => { const value = e.target.value; updateField('material', canonicalMaterial(value)?.material || value); }} placeholder="Search or select a material"/><small>Gemini's highest-confidence candidate maps to the closest canonical material; the ID and category come from that record.</small></label>
        <label className="field"><span>Material ID</span><input readOnly value={canonicalMaterial(form.material)?.material_id ?? (selected.product.material === form.material ? selected.product.material_id ?? '' : '')}/></label>
        <label className="field"><span>Material Category</span><input readOnly value={canonicalMaterial(form.material)?.material_category ?? (selected.product.material === form.material ? selected.product.material_category ?? '' : '')}/></label>
        {materialSuggestion?.status === 'unresolved' && <p className="notice error-notice">Gemini returned “{materialSuggestion.suggested_name || 'an unknown material'}”, which does not match the canonical list. Choose a listed material only if you can confirm it.</p>}
        {materialSuggestion?.status === 'unknown' && <p className="notice">Gemini could not identify the material reliably. Choose from the list if you can confirm the material.</p>}
        <button disabled={saving}>{saving ? 'Saving…' : 'Save changes'}</button></form>
      <div className="images-section"><h3>Product images</h3><div className="image-gallery">{selected.images.map(image => <div className="image-item" key={image.id}><img src={image.url} alt={`Product image ${image.id}`}/>{image.is_primary && <span className="primary-badge">Primary</span>}<div><button className="secondary" onClick={() => void choosePrimary(image)} disabled={image.is_primary}>Set primary</button><button className="danger" onClick={() => void removeImage(image)}>Remove</button></div></div>)}</div>
        <label className="file-label upload-picker">Upload a Picture<input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={e => filePicker(e.target.files, setPendingFiles)}/></label><button type="button" className="secondary camera-button" onClick={() => pendingCameraRef.current?.click()} disabled={busy}>Take a Picture</button><input ref={pendingCameraRef} className="camera-input" type="file" accept="image/*" capture="environment" onChange={e => { if (e.target.files?.[0]) setPendingFiles(current => [...current, e.target.files![0]]); e.target.value = ''; }}/>{pendingFiles.length > 0 && <p>{pendingFiles.length} image(s) ready to upload. Review, remove or retake before uploading.</p>}<div className="preview-strip">{pendingPreviews.map((url, index) => <div className="image-preview" key={url}><img src={url} alt={`Selected upload ${index + 1}`}/><button type="button" className="secondary" onClick={() => setPendingFiles(current => current.filter((_, itemIndex) => itemIndex !== index))}>Remove / retake</button></div>)}</div><button onClick={() => void addImages()} disabled={!pendingFiles.length || busy}>{busy ? 'Uploading…' : 'Upload and analyze'}</button>
        <div className="analysis-row"><select value={analysisImage} onChange={e => setAnalysisImage(Number(e.target.value))} aria-label="Select image to analyze"><option value="">Choose image</option>{selected.images.map(image => <option key={image.id} value={image.id}>{image.is_primary ? 'Primary image' : `Image #${image.id}`}</option>)}</select><button onClick={() => selected && void analyze(selected.product.id, analysisImage ? Number(analysisImage) : undefined)} disabled={analysisBusy || !selected.images.length}>{analysisBusy ? 'Analyzing…' : 'Retry analysis'}</button></div>
      </div>
      <h3>Materials</h3>{selected.materials.length ? selected.materials.map(m => <p key={m.id || m.name}>{m.name} · {m.percentage ?? 'Unknown'}% · {m.verification}</p>) : <p>No composition evidence recorded.</p>}
      <button className="secondary" onClick={async () => { const response = await apiFetch(`${API}/products/${selected.product.id}/assessments`, { method: 'POST' }); if (response.ok) setMessage('Assessment saved: carbon needs method and data; RAPU awaits authoritative methodology.'); else setError('Assessment failed'); }}>Assess sustainability</button>
      <button className="danger" onClick={() => void removeProduct(selected.product)} disabled={busy}>Delete product</button>
    </section></div>}
  </main>;
}


export default function App() {
  const [authState, setAuthState] = useState<'checking' | 'anonymous' | 'authenticated'>('checking');
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    let mounted = true;
    onAuthenticationExpired = () => {
      if (mounted) { csrfToken = ''; setUser(null); setAuthState('anonymous'); }
    };
    apiFetch(`${API}/auth/me`).then(async response => {
      if (!mounted) return;
      if (!response.ok) { setUser(null); setAuthState('anonymous'); return; }
      const result = await response.json();
      csrfToken = result.csrf_token || '';
      setUser(result.user); setAuthState('authenticated');
    }).catch(() => { if (mounted) setAuthState('anonymous'); });
    return () => { mounted = false; onAuthenticationExpired = () => {}; };
  }, []);

  async function login(username: string, password: string): Promise<string | null> {
    const response = await apiFetch(`${API}/auth/login`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const result = await response.json();
    if (!response.ok) return response.status === 401 || response.status === 429
      ? result.detail || 'Invalid username or password.'
      : 'Sign in failed. Check the server and try again.';
    csrfToken = result.csrf_token;
    setUser(result.user); setAuthState('authenticated');
    return null;
  }

  async function logout() {
    try { await apiFetch(`${API}/auth/logout`, { method: 'POST' }); }
    finally { csrfToken = ''; setUser(null); setAuthState('anonymous'); }
  }

  if (authState === 'checking') return <main className="login-shell"><p className="login-loading">Checking your RAKKI session…</p></main>;
  if (authState !== 'authenticated' || !user) return <LoginPage onLogin={login}/>;
  return <Workspace onLogout={() => void logout()}/>;
}
