import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'kol-workbench-tools'
export const inject = ['tools']

const defaultBaseUrl = 'http://127.0.0.1:8766'

function runtimeBaseUrl(config = {}) {
  return String(config.baseUrl || process.env.KOL_WORKBENCH_URL || defaultBaseUrl).replace(/\/+$/, '')
}

async function requestJson(baseUrl, path, options = {}) {
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      ...(options.headers || {}),
    },
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error || `KOL Workbench request failed: ${response.status}`)
  }
  return payload
}

function renderJson(_args, value) {
  return [{ type: 'text', text: JSON.stringify(value, null, 2) }]
}

function registerJsonTool(ctx, spec) {
  ctx.tools.register(defineTool({
    ...spec,
    output: {
      schema: { type: 'object' },
      render: renderJson,
    },
  }))
}

export function apply(ctx, config = {}) {
  const baseUrl = runtimeBaseUrl(config)

  registerJsonTool(ctx, {
    name: 'kol_workbench_status',
    description: 'Read local KOL Workbench status, summary counts, and configured Gmail account placeholders.',
    parameters: {},
    async execute() {
      const [summary, settings] = await Promise.all([
        requestJson(baseUrl, '/api/summary'),
        requestJson(baseUrl, '/api/settings'),
      ])
      return {
        baseUrl,
        summary: summary.summary,
        dbPath: summary.dbPath,
        gmailAccounts: settings.settings?.gmailAccounts || [],
        model: settings.settings?.model || {},
      }
    },
  })

  registerJsonTool(ctx, {
    name: 'kol_list_leads',
    description: 'List KOL leads from the local KOL Workbench with optional query, priority, status, and tag filters.',
    parameters: {
      query: { type: 'string', required: false, description: 'Search handle, email, homepage, or category.' },
      priority: { type: 'string', required: false, description: 'Optional priority filter: high, medium, or low.' },
      status: { type: 'string', required: false, description: 'Optional lead status filter.' },
      tag: { type: 'string', required: false, description: 'Optional tag filter, such as has_email or a market name.' },
    },
    async execute(args) {
      const params = new URLSearchParams()
      for (const key of ['query', 'priority', 'status', 'tag']) {
        if (args[key]) params.set(key, args[key])
      }
      return requestJson(baseUrl, `/api/kols?${params.toString()}`)
    },
  })

  registerJsonTool(ctx, {
    name: 'kol_create_manual_lead',
    description: 'Create one manual KOL lead in the local KOL Workbench, then score and tag it locally.',
    parameters: {
      handle: { type: 'string', required: false, description: 'KOL display name or handle.' },
      email: { type: 'string', required: false, description: 'KOL email address.' },
      platform: { type: 'string', required: false, description: 'Creator platform, default TikTok.' },
      homepageUrl: { type: 'string', required: false, description: 'Creator homepage URL.' },
      country: { type: 'string', required: false, description: 'Market or country.' },
      category: { type: 'string', required: false, description: 'Content category or niche.' },
      followers: { type: 'number', required: false, description: 'Follower count.' },
      sales28d: { type: 'number', required: false, description: 'Estimated 28-day sales.' },
    },
    async execute(args) {
      return requestJson(baseUrl, '/api/kols/manual', {
        method: 'POST',
        body: JSON.stringify(args),
      })
    },
  })

  registerJsonTool(ctx, {
    name: 'kol_generate_gmail_drafts',
    description: 'Generate local Gmail outreach drafts for selected KOL ids. Draft bodies stay in the local KOL Workbench.',
    parameters: {
      kolIds: { type: 'array', required: false, description: 'Selected local KOL ids.' },
      limit: { type: 'number', required: false, description: 'Fallback generation limit when kolIds is empty.' },
      brief: { type: 'string', required: false, description: 'Campaign brief to include in generation.' },
      fromAccount: { type: 'string', required: true, description: 'Configured Gmail sender account from KOL Workbench settings.' },
      language: { type: 'string', required: false, description: 'Draft language code, such as en, zh, de, fr, ja.' },
      templateId: { type: 'string', required: false, description: 'Optional local reply template id.' },
    },
    async execute(args) {
      return requestJson(baseUrl, '/api/drafts/generate', {
        method: 'POST',
        body: JSON.stringify({
          kolIds: args.kolIds || [],
          limit: args.limit || 20,
          brief: args.brief || '',
          fromAccount: args.fromAccount,
          language: args.language || 'en',
          templateId: args.templateId || '',
        }),
      })
    },
  })

  registerJsonTool(ctx, {
    name: 'kol_list_gmail_drafts',
    description: 'List local Gmail drafts, sent records, and archived draft records from the KOL Workbench.',
    parameters: {
      status: { type: 'string', required: false, description: 'Optional draft status: pending_review, sent_recorded, or archived.' },
    },
    async execute(args) {
      const params = new URLSearchParams()
      if (args.status) params.set('status', args.status)
      return requestJson(baseUrl, `/api/drafts?${params.toString()}`)
    },
  })

  registerJsonTool(ctx, {
    name: 'kol_open_gmail_compose',
    description: 'Open a configured local browser/Profile with a prefilled Gmail compose page for a local draft. This does not auto-send.',
    parameters: {
      draftId: { type: 'string', required: true, description: 'Local outreach draft id.' },
      accountEmail: { type: 'string', required: false, description: 'Configured Gmail sender account.' },
    },
    async execute(args) {
      return requestJson(baseUrl, '/api/gmail/open-compose', {
        method: 'POST',
        body: JSON.stringify({
          draftId: args.draftId,
          accountEmail: args.accountEmail || '',
        }),
      })
    },
  })

  registerJsonTool(ctx, {
    name: 'kol_record_gmail_sent',
    description: 'Record a local draft as sent after the user manually sends it in Gmail. This does not call Gmail APIs.',
    parameters: {
      draftId: { type: 'string', required: true, description: 'Local outreach draft id.' },
      fromAccount: { type: 'string', required: true, description: 'Gmail account used by the human sender.' },
    },
    async execute(args) {
      return requestJson(baseUrl, '/api/drafts/approve', {
        method: 'POST',
        body: JSON.stringify({
          draftId: args.draftId,
          fromAccount: args.fromAccount,
        }),
      })
    },
  })

  console.log(`[kol-workbench-tools] registered tools for ${baseUrl}`)
}
