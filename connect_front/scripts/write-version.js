const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')
const pkg = require('../package.json')

const version = process.env.VUE_APP_BUILD_VERSION || `${Date.now()}`
let commit = ''
try { commit = execSync('git rev-parse --short HEAD').toString().trim() } catch (e) {}
const payload = { version, app: pkg.name, pkg: pkg.version, commit, builtAt: new Date().toISOString() }
const out = path.join(__dirname, '..', 'public', 'version.json')
fs.writeFileSync(out, JSON.stringify(payload, null, 2))