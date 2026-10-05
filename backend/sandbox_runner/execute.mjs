import path from 'node:path'
import { performance } from 'node:perf_hooks'
import { Sandbox } from 'railway'

const commands = {
  pytest: ['/opt/agentforge/bin/python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider'],
  'ruff check': ['/opt/agentforge/bin/ruff', 'check', '.'],
}
const maxFileBytes = 256_000
const maxTotalBytes = 12_000_000
const maxLogBytes = 12_000

function validateFiles(files) {
  if (!Array.isArray(files) || files.length === 0 || files.length > 128) {
    throw new Error('Sandbox request must contain 1 to 128 source files.')
  }
  const seen = new Set()
  let totalBytes = 0
  for (const file of files) {
    if (typeof file.path !== 'string' || typeof file.content !== 'string') {
      throw new Error('Sandbox files require a relative path and UTF-8 text content.')
    }
    const normalized = path.posix.normalize(file.path)
    if (normalized !== file.path || normalized.startsWith('/') || normalized.includes('..') || !/^(app|tests)\/.+\.py$/.test(normalized)) {
      throw new Error(`Sandbox path is outside the Python app/tests allowlist: ${file.path}`)
    }
    if (seen.has(normalized)) throw new Error(`Sandbox path was repeated: ${normalized}`)
    seen.add(normalized)
    const size = Buffer.byteLength(file.content, 'utf8')
    if (size > maxFileBytes) throw new Error(`Sandbox file exceeds the size limit: ${normalized}`)
    totalBytes += size
  }
  if (totalBytes > maxTotalBytes) throw new Error('Sandbox source exceeds the total size limit.')
}

async function main() {
  const started = performance.now()
  let sandbox
  try {
    const inputChunks = []
    for await (const chunk of process.stdin) inputChunks.push(chunk)
    const input = JSON.parse(Buffer.concat(inputChunks).toString('utf8'))
    if (!Object.hasOwn(commands, input.command)) throw new Error('Command is not allowlisted.')
    validateFiles(input.files)

    const token = process.env.RAILWAY_PROJECT_TOKEN
    const environmentId = process.env.RAILWAY_ENVIRONMENT_ID
    if (!token || !environmentId) throw new Error('Railway project token or environment ID is not configured.')

    const client = { token, authType: 'project-token', environmentId }
    const template = await Sandbox.template()
      .withPackages('python3', 'python3-venv')
      .run('python3 -m venv /opt/agentforge')
      .run("/opt/agentforge/bin/pip install --disable-pip-version-check 'fastapi>=0.115,<0.120' 'httpx>=0.28,<1' 'sqlalchemy>=2.0,<3' 'psycopg[binary]>=3.2,<4' 'uvicorn>=0.34,<1' 'pytest>=8.3,<9' 'ruff>=0.9,<1'")
      .build(client)

    sandbox = await Sandbox.create(template, {
      ...client,
      idleTimeoutMinutes: 2,
      networkIsolation: 'ISOLATED',
      env: { PYTHONDONTWRITEBYTECODE: '1', SAMPLE_DATABASE_URL: 'sqlite://' },
    })
    await sandbox.files.mkdir('/workspace')
    const directories = [...new Set(input.files.map((file) => `/workspace/${path.posix.dirname(file.path)}`))]
    await Promise.all(directories.map((directory) => sandbox.files.mkdir(directory)))
    await Promise.all(input.files.map((file) => sandbox.files.write(`/workspace/${file.path}`, file.content)))
    const result = await sandbox.exec(commands[input.command].join(' '), {
      cwd: '/workspace',
      timeoutSec: Math.max(5, Math.min(Number(input.timeoutSeconds) || 30, 120)),
      env: { RUFF_CACHE_DIR: '/tmp/ruff-cache' },
    })
    process.stdout.write(JSON.stringify({
      status: result.timedOut ? 'timeout' : result.exitCode === 0 ? 'passed' : 'failed',
      exit_code: result.exitCode,
      stdout: result.stdout.slice(-maxLogBytes),
      stderr: result.stderr.slice(-maxLogBytes),
      duration_seconds: Math.round((performance.now() - started) / 10) / 100,
    }))
  } catch (error) {
    process.stdout.write(JSON.stringify({
      status: 'failed', exit_code: null, stdout: '',
      stderr: String(error?.message || error).slice(-maxLogBytes),
      duration_seconds: Math.round((performance.now() - started) / 10) / 100,
    }))
  } finally {
    if (sandbox) await sandbox.destroy().catch(() => {})
  }
}

await main()
