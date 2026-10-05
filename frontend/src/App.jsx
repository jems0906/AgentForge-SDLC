import { useEffect, useState } from 'react'
import { flexRender, getCoreRowModel, useReactTable } from '@tanstack/react-table'
import {
  Activity, ArrowDownRight, ArrowRight, ArrowUpRight, Check, CheckCircle2,
  CircleAlert, Clock3, Cpu, GitMerge, GitPullRequest, LayoutDashboard,
  ListTodo, Play, Plus, RotateCcw, Rocket, ShieldCheck, TerminalSquare,
  Workflow, X, XCircle,
} from 'lucide-react'
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'

const API = import.meta.env.VITE_API_URL || ''
const nav = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'tasks', label: 'Agent tasks', icon: ListTodo },
  { id: 'workflows', label: 'Workflows', icon: Workflow },
  { id: 'reviews', label: 'PR reviews', icon: GitPullRequest },
  { id: 'quality', label: 'CI quality', icon: Activity },
  { id: 'sandbox', label: 'Sandbox', icon: TerminalSquare },
  { id: 'providers', label: 'Providers', icon: Cpu },
]

async function request(path, options) {
  const response = await fetch(`${API}/api${path}`, {
    headers: { 'Content-Type': 'application/json' }, ...options,
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`)
  return body
}

const taskExamples = [
  { title: 'Add lease renewal reminder endpoint', type: 'feature', description: 'Notify property managers when a lease enters the 60-day renewal window.' },
  { title: 'Fix maintenance ticket priority bug', type: 'bugfix', description: 'Normalize incoming priority values and reject unsupported levels.' },
  { title: 'Refactor rent payment validation', type: 'refactor', description: 'Make payment amount rules explicit and cover boundary cases.' },
]

function statusClass(status = '') {
  return `status status-${status.toLowerCase().replaceAll('_', '-')}`
}

function App() {
  const [page, setPage] = useState('overview')
  const [data, setData] = useState({ tasks: [], reviews: [], workflows: [], quality: null, providers: [], integrations: {}, runs: [] })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [taskFormOpen, setTaskFormOpen] = useState(false)

  async function refresh() {
    const paths = ['/tasks', '/reviews', '/workflows', '/dashboards/ci-quality', '/providers', '/integrations', '/sandbox/runs']
    const results = await Promise.allSettled(paths.map((path) => request(path)))
    if (results[0].status === 'rejected') setError(results[0].reason.message)
    else setError('')
    setData({
      tasks: results[0].status === 'fulfilled' ? results[0].value : [],
      reviews: results[1].status === 'fulfilled' ? results[1].value : [],
      workflows: results[2].status === 'fulfilled' ? results[2].value : [],
      quality: results[3].status === 'fulfilled' ? results[3].value : null,
      providers: results[4].status === 'fulfilled' ? results[4].value : [],
      integrations: results[5].status === 'fulfilled' ? results[5].value : {},
      runs: results[6].status === 'fulfilled' ? results[6].value : [],
    })
  }

  useEffect(() => {
    refresh()
    const timer = window.setInterval(refresh, 8000)
    return () => window.clearInterval(timer)
  }, [])

  async function createTask(task) {
    setBusy(true)
    try {
      await request('/tasks', { method: 'POST', body: JSON.stringify(task) })
      setNotice('Task queued for the agent worker.')
      setPage('tasks')
      await refresh()
    } catch (reason) { setError(reason.message) }
    finally { setBusy(false) }
  }

  async function decide(review, decision) {
    setBusy(true)
    try {
      await request(`/reviews/${review.id}/decision`, { method: 'POST', body: JSON.stringify({ decision }) })
      setNotice(`Review ${decision.replace('_', ' ')}.`)
      await refresh()
    } catch (reason) { setError(reason.message) }
    finally { setBusy(false) }
  }

  async function runCommand(command) {
    setBusy(true)
    try {
      await request('/sandbox/execute', { method: 'POST', body: JSON.stringify({ command }) })
      setNotice(`${command} finished.`)
      await refresh()
    } catch (reason) { setError(reason.message) }
    finally { setBusy(false) }
  }

  const selected = nav.find((item) => item.id === page) || nav[0]
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#overview" onClick={() => setPage('overview')}>
          <span className="brand-mark"><Workflow size={19} strokeWidth={2.4} /></span>
          <span><strong>agentforge</strong><small>SDLC CONTROL PLANE</small></span>
        </a>
        <div className="workspace-label">WORKSPACE</div>
        <div className="workspace-switch"><span className="workspace-avatar">H</span><span><b>Hearthside</b><small>Property platform</small></span><span className="switch-caret">⌄</span></div>
        <div className="nav-label">OPERATIONS</div>
        <nav className="nav-list" aria-label="Main navigation">
          {nav.map(({ id, label, icon: Icon }) => (
            <button key={id} className={`nav-item ${page === id ? 'active' : ''}`} onClick={() => { setPage(id); setTaskFormOpen(false); setNotice('') }}>
              <Icon size={17} strokeWidth={1.9} /><span>{label}</span>
              {id === 'reviews' && data.reviews.filter((review) => review.status === 'review').length > 0 && <b className="nav-count">{data.reviews.filter((review) => review.status === 'review').length}</b>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="connection-indicator"><span className={error ? 'dot dot-red' : 'dot'}></span><span>{error ? 'API unavailable' : 'API connected'}</span></div>
          <div className="user-row"><div className="user-avatar">JD</div><span><b>Jordan Davis</b><small>Platform engineer</small></span><span className="user-menu">•••</span></div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb"><span>Hearthside</span><span className="crumb-sep">/</span><b>{selected.label}</b></div>
          <div className="topbar-actions"><span className="env-pill"><span className="dot"></span> MOCK ENVIRONMENT</span><button className="icon-button" title="Refresh data" onClick={refresh}><RotateCcw size={16} /></button><div className="top-date">OCT 03, 2026</div></div>
        </header>

        <div className="content-wrap">
          {(error || notice) && <div className={`notice ${error ? 'notice-error' : 'notice-success'}`} role="status"><span>{error || notice}</span><button onClick={() => { setError(''); setNotice('') }} title="Dismiss"><X size={15} /></button></div>}
          {page === 'overview' && <Overview data={data} setPage={setPage} sandboxReady={data.integrations.sandbox?.configured !== false} openTask={() => { setTaskFormOpen(true); setPage('tasks') }} />}
          {page === 'tasks' && <TasksPage tasks={data.tasks} providers={data.providers} sandboxReady={data.integrations.sandbox?.configured !== false} createTask={createTask} busy={busy} formOpen={taskFormOpen} setFormOpen={setTaskFormOpen} />}
          {page === 'workflows' && <WorkflowsPage workflows={data.workflows} sandboxReady={data.integrations.sandbox?.configured !== false} createTask={createTask} busy={busy} />}
          {page === 'reviews' && <ReviewsPage reviews={data.reviews} tasks={data.tasks} integrations={data.integrations} decide={decide} busy={busy} />}
          {page === 'quality' && <QualityPage quality={data.quality} tasks={data.tasks} />}
          {page === 'sandbox' && <SandboxPage runs={data.runs} integrations={data.integrations} runCommand={runCommand} busy={busy} />}
          {page === 'providers' && <ProvidersPage providers={data.providers} integrations={data.integrations} />}
        </div>
        <footer className="footer"><span>AGENTFORGE SDLC <span className="footer-dot">/</span> WORKSPACE: HEARTHSIDE</span><span>CONTROL PLANE <span className="footer-dot">·</span> V0.1.0</span></footer>
      </main>
    </div>
  )
}

function PageHeading({ eyebrow, title, description, action }) {
  return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action}</div>
}

function Overview({ data, setPage, openTask, sandboxReady }) {
  const quality = data.quality || {}
  const needsReview = data.reviews.filter((review) => review.status === 'review').length
  const active = data.tasks.filter((task) => ['queued', 'running', 'in_review'].includes(task.status)).length
  const chartData = (quality.runs || []).slice(-10).map((run, index) => ({ run: `#${index + 1}`, pass: run.status === 'passed' ? 100 : 0 }))
  return <>
    <PageHeading eyebrow="SATURDAY, OCTOBER 3, 2026" title="Good morning, Jordan" description={sandboxReady ? 'Your agent workflows are in view. Here is what needs attention.' : 'Task intake is paused until an isolated Docker runner is connected.'} action={<button className="button button-primary" disabled={!sandboxReady} title={sandboxReady ? 'New task' : 'Configure the isolated Docker runner first'} onClick={openTask}><Plus size={16} /> New task</button>} />
    <div className="metric-grid">
      <Metric label="Open tasks" value={active} note={`${data.tasks.length} total in queue`} icon={ListTodo} accent="green" />
      <Metric label="Awaiting review" value={needsReview} note="Human approval required" icon={GitPullRequest} accent="orange" />
      <Metric label="Test pass rate" value={`${quality.test_pass_rate ?? 100}%`} note={`${quality.failed_runs || 0} failed runs`} icon={ShieldCheck} accent="blue" />
      <Metric label="Agent success" value={`${quality.agent_success_rate ?? 100}%`} note={`${quality.tasks_total || 0} workflow runs`} icon={Activity} accent="red" />
    </div>
    <div className="overview-grid">
      <section className="panel quality-panel">
        <div className="panel-header"><div><div className="section-kicker">DELIVERY HEALTH</div><h2>Validation trend</h2></div><button className="text-button" onClick={() => setPage('quality')}>View quality <ArrowRight size={14} /></button></div>
        <div className="chart-summary"><strong>{quality.test_pass_rate ?? 100}%</strong><span className="trend-up"><ArrowUpRight size={14} /> stable</span><small>Recent sandbox runs</small></div>
        <div className="chart-wrap">{chartData.length ? <ResponsiveContainer width="100%" height="100%"><AreaChart data={chartData} margin={{ top: 12, right: 8, bottom: 0, left: -25 }}><defs><linearGradient id="passFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#7fc97f" stopOpacity={0.32} /><stop offset="100%" stopColor="#7fc97f" stopOpacity={0.01} /></linearGradient></defs><CartesianGrid stroke="#e7ebe6" vertical={false} /><XAxis dataKey="run" tickLine={false} axisLine={false} tick={{ fill: '#89918a', fontSize: 11 }} /><YAxis domain={[0, 100]} tickLine={false} axisLine={false} tick={{ fill: '#89918a', fontSize: 10 }} /><Tooltip contentStyle={{ border: '1px solid #e2e7e1', borderRadius: 5, fontSize: 12 }} /><Area type="monotone" dataKey="pass" stroke="#478b5f" strokeWidth={2} fill="url(#passFill)" /></AreaChart></ResponsiveContainer> : <div className="chart-empty"><Activity size={20} /><span>Run a sandbox check to start the trend.</span></div>}</div>
      </section>
      <section className="panel attention-panel">
        <div className="panel-header"><div><div className="section-kicker">NEEDS ATTENTION</div><h2>Review queue <span className="count-bubble">{needsReview}</span></h2></div><button className="icon-button" title="Open reviews" onClick={() => setPage('reviews')}><ArrowUpRight size={16} /></button></div>
        {data.reviews.filter((review) => review.status === 'review').slice(0, 3).map((review) => {
          const task = data.tasks.find((item) => item.id === review.task_id)
          return <button className="attention-item" key={review.id} onClick={() => setPage('reviews')}><span className="attention-icon"><GitPullRequest size={15} /></span><span className="attention-copy"><b>{task?.title || review.summary}</b><small>PR #{review.id} · {task?.task_type || 'workflow'}</small></span><ArrowRight size={14} className="attention-arrow" /></button>
        })}
        {!needsReview && <div className="empty-inline"><CheckCircle2 size={18} /><span>Nothing waiting on approval.</span></div>}
        <button className="panel-link" onClick={() => setPage('reviews')}>Open review queue <ArrowRight size={14} /></button>
      </section>
    </div>
    <section className="panel recent-panel">
      <div className="panel-header"><div><div className="section-kicker">WORKSPACE ACTIVITY</div><h2>Recent tasks</h2></div><button className="text-button" onClick={() => setPage('tasks')}>All tasks <ArrowRight size={14} /></button></div>
      <TaskTable tasks={data.tasks.slice(0, 5)} />
      {!data.tasks.length && <div className="empty-inline empty-table"><span>Start with a property-management task and the worker will prepare it for review.</span><button className="button button-secondary" onClick={() => setPage('tasks')}><Plus size={15} /> Create task</button></div>}
    </section>
  </>
}

function Metric({ label, value, note, icon: Icon, accent }) {
  return <div className="metric-card"><div className={`metric-icon accent-${accent}`}><Icon size={17} /></div><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-note">{note}</div></div>
}

function TaskTable({ tasks }) {
  const columns = [
    { accessorKey: 'title', header: 'TASK', cell: ({ row }) => <><b className="task-name">{row.original.title}</b><small className="task-id">AG-{String(row.original.id).padStart(4, '0')}</small></> },
    { accessorKey: 'task_type', header: 'TYPE', cell: ({ getValue }) => <span className="type-text">{getValue()}</span> },
    { accessorKey: 'provider', header: 'PROVIDER', cell: ({ getValue }) => <span className="provider-cell"><span className="provider-mini">{getValue().slice(0, 1).toUpperCase()}</span>{getValue()}</span> },
    { accessorKey: 'status', header: 'STATUS', cell: ({ getValue }) => <span className={statusClass(getValue())}><i></i>{getValue().replaceAll('_', ' ')}</span> },
    { accessorKey: 'created_at', header: 'CREATED', cell: ({ getValue }) => <span className="muted-cell">{new Date(getValue()).toLocaleDateString()}</span> },
  ]
  const table = useReactTable({ data: tasks, columns, getCoreRowModel: getCoreRowModel() })
  return <div className="table-scroll"><table><thead>{table.getHeaderGroups().map((group) => <tr key={group.id}>{group.headers.map((header) => <th key={header.id}>{flexRender(header.column.columnDef.header, header.getContext())}</th>)}</tr>)}</thead><tbody>{table.getRowModel().rows.map((row) => <tr key={row.id}>{row.getVisibleCells().map((cell) => <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}</tr>)}</tbody></table></div>
}

function TasksPage({ tasks, providers, sandboxReady, createTask, busy, formOpen, setFormOpen }) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [type, setType] = useState('feature')
  const [provider, setProvider] = useState('mock')
  const [filter, setFilter] = useState('all')
  const completedStatuses = ['approved', 'merged', 'deployed', 'rejected', 'rolled_back', 'failed']
  const visibleTasks = tasks.filter((task) => filter === 'all' || (filter === 'active' ? ['queued', 'running', 'in_review'].includes(task.status) : completedStatuses.includes(task.status)))
  function submit(event) { event.preventDefault(); if (!title.trim()) return; createTask({ title, description, task_type: type, provider }); setTitle(''); setDescription(''); setFormOpen(false) }
  return <>
    <PageHeading eyebrow="EXECUTION QUEUE" title="Agent tasks" description={sandboxReady ? 'Define a coding task, select a workflow, and let the worker prepare a reviewable change.' : 'Task intake is paused until an isolated Docker runner is connected.'} action={<button className="button button-primary" disabled={!sandboxReady} title={sandboxReady ? 'New task' : 'Configure the isolated Docker runner first'} onClick={() => setFormOpen(!formOpen)}><Plus size={16} /> New task</button>} />
    {formOpen && <form className="panel task-form" onSubmit={submit}><div className="form-header"><div><div className="section-kicker">NEW AGENT RUN</div><h2>Define the work</h2></div><button type="button" className="icon-button" title="Close" onClick={() => setFormOpen(false)}><X size={16} /></button></div><label>Task title<input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="e.g. Add lease renewal reminders" minLength="3" required maxLength="180" /></label><label>Task description<textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Describe the expected behavior and constraints" rows="3" maxLength="8000" /></label><div className="form-row"><label>Workflow type<select value={type} onChange={(event) => setType(event.target.value)}>{['feature', 'bugfix', 'refactor', 'test', 'integration'].map((item) => <option key={item} value={item}>{item[0].toUpperCase() + item.slice(1)}</option>)}</select></label><label>AI provider<select value={provider} onChange={(event) => setProvider(event.target.value)}>{providers.filter((item) => item.configured).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label></div><div className="form-footer"><span>Changes will stop at the human approval gate.</span><button className="button button-primary" disabled={busy || !sandboxReady}><Play size={14} /> Queue task</button></div></form>}
    <div className="filter-row"><div className="filter-tabs"><button className={filter === 'all' ? 'filter-active' : ''} onClick={() => setFilter('all')}>All tasks <span>{tasks.length}</span></button><button className={filter === 'active' ? 'filter-active' : ''} onClick={() => setFilter('active')}>In progress <span>{tasks.filter((task) => ['queued', 'running', 'in_review'].includes(task.status)).length}</span></button><button className={filter === 'completed' ? 'filter-active' : ''} onClick={() => setFilter('completed')}>Completed <span>{tasks.filter((task) => completedStatuses.includes(task.status)).length}</span></button></div><span className="subtle-label">AUTO-REFRESH 8S</span></div>
    <section className="panel table-panel"><TaskTable tasks={visibleTasks} />{!tasks.length && <div className="empty-state"><div className="empty-mark"><ListTodo size={21} /></div><h3>No tasks yet</h3><p>Choose a sample task to start your first agent run.</p><div className="example-chips">{taskExamples.map((task) => <button key={task.type} onClick={() => { setTitle(task.title); setDescription(task.description); setType(task.type); setFormOpen(true) }}>{task.title}<ArrowUpRight size={13} /></button>)}</div></div>}{tasks.length > 0 && !visibleTasks.length && <div className="empty-inline">No tasks in this status group.</div>}</section>
  </>
}

function WorkflowsPage({ workflows, sandboxReady, createTask, busy }) {
  return <>
    <PageHeading eyebrow="ORCHESTRATION" title="Workflow templates" description={sandboxReady ? 'Repeatable agent sequences with explicit validation and human approval gates.' : 'Workflow launch is paused until an isolated Docker runner is connected.'} />
    <div className="workflow-grid">{workflows.map((flow, index) => <article className="panel workflow-card" key={flow.id}><div className="workflow-card-top"><span className={`workflow-index workflow-index-${index % 4}`}>0{index + 1}</span><span className="workflow-category">{flow.id.toUpperCase()}</span></div><h2>{flow.name}</h2><p>{flow.description}</p><div className="step-list">{flow.steps.map((step, stepIndex) => <div className="step-row" key={step}><span className={`step-number ${step === 'approval' ? 'step-gate' : ''}`}>{step === 'approval' ? <ShieldCheck size={13} /> : String(stepIndex + 1).padStart(2, '0')}</span><span>{step.replaceAll('_', ' ')}</span>{step === 'approval' && <small>HUMAN GATE</small>}</div>)}</div><button className="button button-secondary workflow-launch" disabled={busy || !sandboxReady} title={sandboxReady ? 'Start workflow' : 'Configure the isolated Docker runner first'} onClick={() => createTask({ title: `${flow.name}: property-management task`, description: flow.description, task_type: flow.id, provider: 'mock' })}><Play size={14} /> Start workflow</button></article>)}</div>
    <div className="callout-strip"><ShieldCheck size={17} /><span>Approval is required before merge. Deploy and rollback are tracked as separate lifecycle decisions.</span><ArrowRight size={15} /></div>
  </>
}

function ReviewsPage({ reviews, tasks, integrations, decide, busy }) {
  const [selected, setSelected] = useState(null)
  const review = reviews.find((item) => item.id === selected) || reviews.find((item) => item.status === 'review') || reviews[0]
  const task = review && tasks.find((item) => item.id === review.task_id)
  const next = review?.status === 'review' ? ['approve', 'request_changes', 'reject'] : review?.status === 'approved' ? ['merge'] : review?.status === 'merged' ? ['deploy'] : review?.status === 'deployed' ? ['rollback'] : []
  const labels = { approve: 'Approve', request_changes: 'Request changes', reject: 'Reject', merge: 'Merge PR', deploy: 'Mark deployed', rollback: 'Record rollback' }
  return <>
    <PageHeading eyebrow="HUMAN APPROVAL GATE" title="Pull request reviews" description="Inspect agent proposals, test outcomes, and reviewer notes before advancing a change." />
    {!reviews.length ? <section className="panel empty-state review-empty"><div className="empty-mark"><GitPullRequest size={21} /></div><h3>No reviews to inspect</h3><p>Completed agent runs appear here as draft pull requests.</p></section> : <div className="review-layout"><section className="panel review-list"><div className="review-list-head"><span>CHANGE QUEUE</span><span>{reviews.length} PR{reviews.length === 1 ? '' : 's'}</span></div>{reviews.map((item) => { const associated = tasks.find((entry) => entry.id === item.task_id); return <button key={item.id} className={`review-list-item ${review?.id === item.id ? 'selected' : ''}`} onClick={() => setSelected(item.id)}><span className="review-list-icon"><GitPullRequest size={15} /></span><span className="review-list-copy"><b>{associated?.title || item.summary}</b><small>PR #{item.id} · AG-{String(item.task_id).padStart(4, '0')}</small></span><span className={statusClass(item.status)}><i></i>{item.status.replaceAll('_', ' ')}</span></button>})}</section>
      {review && <section className="panel diff-panel"><div className="diff-heading"><div><div className="section-kicker">PULL REQUEST #{review.id}</div><h2>{task?.title || review.summary}</h2><div className="diff-meta"><span className={statusClass(review.status)}><i></i>{review.status.replaceAll('_', ' ')}</span><span>by agentforge/{task?.provider || 'mock'}</span><span>·</span><span>{new Date(review.created_at).toLocaleDateString()}</span></div></div><button className="icon-button" title="Refresh" onClick={() => window.location.reload()}><RotateCcw size={15} /></button></div>
        {task?.outputs?.github?.url && <a className="external-pr-link" href={task.outputs.github.url} target="_blank" rel="noreferrer">Open GitHub draft PR ↗</a>}
        <div className="review-tabs"><span className="tab-selected">Conversation <b>{review.comments.length}</b></span><span>Files changed <b>{task?.outputs?.proposal?.files_changed?.length || 0}</b></span><span>Checks <b>{task?.outputs?.tests?.status === 'passed' ? '✓' : '!'}</b></span></div>
        {task?.outputs?.tests && <div className={`test-banner ${task.outputs.tests.status === 'passed' ? 'test-pass' : 'test-fail'}`}>{task.outputs.tests.status === 'passed' ? <CheckCircle2 size={16} /> : <CircleAlert size={16} />}<span><b>Sandbox tests {task.outputs.tests.status}</b><small>{task.outputs.tests.command || 'pytest'} · exit {task.outputs.tests.exit_code ?? '—'}</small></span></div>}
        <div className="review-summary"><span className="avatar-agent">AF</span><div><b>AgentForge Bot <small>bot</small></b><p>{review.summary}</p></div></div>
        {task?.outputs?.plan?.map((step, index) => <div className="plan-item" key={step.title}><span>{String(index + 1).padStart(2, '0')}</span><div><b>{step.title}</b><p>{step.detail}</p></div></div>)}
        <div className="diff-file-head"><span>PROPOSED PATCH</span><span>MOCK PROVIDER</span></div><pre className="diff-code"><code>{review.diff || '# No diff was generated.'}</code></pre>
        <div className="review-comments">{review.comments.map((comment, index) => <div className="review-comment" key={index}><CircleAlert size={15} /><span><b>{comment.severity || 'note'}</b> {comment.file && `· ${comment.file}`}<p>{comment.comment}</p></span></div>)}</div>
        {!!next.length && <div className="review-actions">{next.map((decision) => { const unavailable = decision === 'merge' ? !integrations.github?.configured || !task?.outputs?.github : ['deploy', 'rollback'].includes(decision) && !integrations.railway?.configured; const unavailableTitle = decision === 'merge' ? 'Configure GitHub and create a draft PR to enable merge' : 'Configure Railway service credentials to enable this action'; return <button key={decision} className={`button ${decision === 'approve' || decision === 'merge' || decision === 'deploy' ? 'button-primary' : 'button-secondary'}`} title={unavailable ? unavailableTitle : labels[decision]} disabled={busy || unavailable} onClick={() => decide(review, decision)}>{decision === 'merge' ? <GitMerge size={15} /> : decision === 'deploy' ? <Rocket size={15} /> : decision === 'rollback' ? <RotateCcw size={15} /> : decision === 'reject' ? <XCircle size={15} /> : decision === 'approve' ? <Check size={15} /> : <ArrowDownRight size={15} />}{labels[decision]}</button>})}</div>}
      </section>}</div>}
  </>
}

function QualityPage({ quality, tasks }) {
  const chartData = (quality?.runs || []).slice(-14).map((run, index) => ({ run: `Run ${index + 1}`, value: run.status === 'passed' ? 100 : 0 }))
  return <>
    <PageHeading eyebrow="DELIVERY SIGNALS" title="CI quality" description="Track validation health, workflow reliability, and delivery time across agent runs." />
    <div className="metric-grid quality-metrics"><Metric label="Test pass rate" value={`${quality?.test_pass_rate ?? 100}%`} note="Across sandbox runs" icon={ShieldCheck} accent="green" /><Metric label="Lint failures" value={quality?.lint_failures ?? 0} note="Allowlisted lint runs" icon={CircleAlert} accent="orange" /><Metric label="Agent success" value={`${quality?.agent_success_rate ?? 100}%`} note="Completed vs failed" icon={Activity} accent="blue" /><Metric label="Avg. task time" value={`${quality?.average_task_seconds ?? 0}s`} note="Completed workflows" icon={Clock3} accent="red" /></div>
    {!!quality?.alerts?.length && <div className="alert-banner"><CircleAlert size={17} /><span><b>Threshold alert</b>{quality.alerts.join(', ')}</span></div>}
    <section className="panel quality-detail"><div className="panel-header"><div><div className="section-kicker">RUN HISTORY</div><h2>Sandbox validation</h2></div><span className="subtle-label">LAST {quality?.runs?.length || 0} RUNS</span></div><div className="quality-chart">{chartData.length ? <ResponsiveContainer width="100%" height="100%"><AreaChart data={chartData} margin={{ top: 16, right: 16, bottom: 0, left: 0 }}><CartesianGrid stroke="#e8ece7" vertical={false} /><XAxis dataKey="run" tickLine={false} axisLine={false} tick={{ fill: '#838c84', fontSize: 11 }} /><YAxis domain={[0, 100]} tickLine={false} axisLine={false} tick={{ fill: '#838c84', fontSize: 11 }} /><Tooltip /><Area dataKey="value" name="Passed" type="stepAfter" stroke="#48875d" fill="#dcebdd" /></AreaChart></ResponsiveContainer> : <div className="chart-empty"><Activity size={20} /><span>No run data yet. Start a sandbox check to populate quality metrics.</span></div>}</div></section>
    <section className="panel recent-panel"><div className="panel-header"><div><div className="section-kicker">AGENT EXECUTION</div><h2>Task outcomes</h2></div><span className="subtle-label">{tasks.length} TOTAL TASKS</span></div><TaskTable tasks={tasks.slice(0, 8)} /></section>
  </>
}

function SandboxPage({ runs, integrations, runCommand, busy }) {
  const commands = ['pytest', 'ruff check']
  const sandboxReady = integrations.sandbox?.configured !== false
  return <>
    <PageHeading eyebrow="CONSTRAINED EXECUTION" title="Sandbox console" description="Run pre-approved checks against the bundled property-management sample repository." />
    <div className="sandbox-layout"><section className="panel sandbox-controls"><div className="section-kicker">ALLOWLISTED COMMANDS</div><h2>Run a check</h2><p>Commands execute without a shell, inside the bundled sample repo, with a 30-second timeout and filtered environment.</p>{!sandboxReady && <div className="notice notice-error">Configure a private TLS Docker runner before enabling sandbox execution.</div>}{commands.map((command) => <div className="command-row" key={command}><code><span className="prompt">$</span> {command}</code><button className="icon-button run-button" title={`Run ${command}`} disabled={busy || !sandboxReady} onClick={() => runCommand(command)}><Play size={15} /></button></div>)}<div className="sandbox-footnote"><ShieldCheck size={15} /> Arbitrary paths and shell commands are rejected.</div></section>
      <section className="panel run-history"><div className="panel-header"><div><div className="section-kicker">EXECUTION LOG</div><h2>Recent runs</h2></div><span className="subtle-label">{runs.length} RECORDED</span></div>{runs.length ? runs.map((run) => <div className="run-item" key={run.id}><span className={`run-state ${run.status === 'passed' ? 'run-ok' : 'run-bad'}`}>{run.status === 'passed' ? <Check size={13} /> : <X size={13} />}</span><span className="run-copy"><b>{run.command}</b><small>{new Date(run.created_at).toLocaleString()} · {run.duration_seconds}s</small>{(run.stderr || run.stdout) && <pre>{(run.stderr || run.stdout).slice(0, 500)}</pre>}</span><span className={statusClass(run.status)}><i></i>{run.status}</span></div>) : <div className="empty-state"><div className="empty-mark"><TerminalSquare size={20} /></div><h3>Console is quiet</h3><p>Choose an allowlisted command to validate the sample repo.</p></div>}</section></div>
  </>
}

function ProvidersPage({ providers, integrations }) {
  const icons = { mock: 'M', anthropic: 'A', openai: 'O', gemini: 'G' }
  return <>
    <PageHeading eyebrow="MODEL ROUTING" title="Provider adapters" description="Choose a configured provider per task. API keys are managed as service environment variables." />
    <section className="panel provider-panel"><div className="panel-header"><div><div className="section-kicker">AVAILABLE PROVIDERS</div><h2>Connection status</h2></div><span className="env-pill"><span className="dot"></span> SECRETS STAY SERVER-SIDE</span></div>{providers.map((provider) => <div className="provider-row" key={provider.id}><span className={`provider-logo provider-${provider.id}`}>{icons[provider.id]}</span><span className="provider-info"><b>{provider.name}</b><small>{provider.id === 'mock' ? 'Deterministic responses · no API key needed' : `Configure ${provider.id.toUpperCase()}_API_KEY on the API service`}</small></span>{provider.default && <span className="default-tag">DEFAULT</span>}<span className={`provider-state ${provider.configured ? 'connected' : ''}`}><i></i>{provider.configured ? 'Configured' : 'Not configured'}</span></div>)}</section>
    <section className="panel provider-panel integration-panel"><div className="panel-header"><div><div className="section-kicker">DELIVERY CONNECTIONS</div><h2>GitHub, Railway & Sandbox</h2></div></div>{[['github', 'GitHub pull requests', 'GITHUB_TOKEN + GITHUB_REPOSITORY', integrations.github], ['railway', 'Railway deployments', 'RAILWAY_PROJECT_TOKEN + project, environment, and service IDs', integrations.railway], ['sandbox', 'Isolated Docker runner', 'DOCKER_HOST + TLS certificate settings', integrations.sandbox]].map(([id, name, settings, state]) => <div className="provider-row" key={id}><span className={`provider-logo provider-${id}`}>{id === 'github' ? 'GH' : id === 'railway' ? 'R' : 'D'}</span><span className="provider-info"><b>{name}</b><small>{state?.configured ? state.repository || state.service_id || state.mode || 'Configured' : `Set ${settings} on the API service`}</small></span><span className={`provider-state ${state?.configured ? 'connected' : ''}`}><i></i>{state?.configured ? 'Configured' : 'Not configured'}</span></div>)}</section>
    <div className="provider-note"><CircleAlert size={17} /><span><b>Provider keys stay server-side.</b> Remote adapters return plans, proposed diffs, and review comments; changes run only inside an isolated task workspace.</span></div>
  </>
}

export default App