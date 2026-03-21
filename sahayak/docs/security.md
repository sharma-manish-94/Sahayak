# Security Hardening

## Overview

Sahayak is designed for a demo environment but follows defense-in-depth principles. The gateway is locked down to prevent unauthorized access, tool abuse, and data leakage.

## Security Measures

### 1. Localhost-Only Gateway

```yaml
gateway:
  bind: localhost
```

The OpenClaw gateway binds only to `127.0.0.1`. It is not reachable from the network. WhatsApp messages arrive through the WhatsApp extension's webhook infrastructure, which has its own authentication.

### 2. Disabled ClawHub

```yaml
skills:
  allowBundled:
    - sahayak-lang
    - sahayak-gov
```

Only Sahayak-specific skills are allowed. The ClawHub marketplace is not loaded, preventing untrusted skill installation.

### 3. Plugin Allowlist

```yaml
plugins:
  allow:
    - whatsapp
```

Only the WhatsApp plugin is loaded. Other plugins (Discord, Telegram, Slack, etc.) are not available, reducing the attack surface.

### 4. Tool Deny List

```yaml
tools:
  deny:
    - bash
    - computer
    - file_write
    - file_edit
```

Dangerous tools are explicitly denied. The agent cannot:
- Execute shell commands (`bash`)
- Control the computer (`computer`)
- Write files (`file_write`)
- Edit files (`file_edit`)

This prevents prompt injection attacks from gaining system access.

### 5. WhatsApp Number Allowlist

```yaml
channels:
  whatsapp:
    enabled: true
    dmPolicy: open
    groupPolicy: disabled
    # allowFrom: ["+91XXXXXXXXXX"]  # Uncomment to restrict
```

- Group messages are disabled (prevents spam/abuse in group chats)
- `allowFrom` can restrict to specific phone numbers for demo

### 6. No Group Messages

```yaml
channels:
  whatsapp:
    groupPolicy: disabled
```

The bot only responds to direct messages. Group messages are ignored, preventing:
- Uncontrolled message volume
- Context confusion from multi-party conversations
- Potential abuse via group additions

### 7. Secrets via Environment Variables

All API keys are loaded from environment variables — never hardcoded in config:

| Variable | Purpose |
|----------|---------|
| `DATA_GOV_IN_API_KEY` | data.gov.in API access |
| `BHASHINI_ULCA_USER_ID` | Bhashini ULCA user ID |
| `BHASHINI_ULCA_API_KEY` | Bhashini ULCA API key |
| `OPENAI_API_KEY` | Whisper ASR fallback |
| `ANTHROPIC_API_KEY` | Claude Sonnet for agent |

### 8. Container Isolation (Docker)

```yaml
# docker-compose.sahayak.yml
services:
  govdata-india:
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
```

Each container runs with:
- **Read-only filesystem**: Cannot write to disk
- **No new privileges**: Cannot escalate via setuid/setgid
- **All capabilities dropped**: Minimal Linux capabilities

## Threat Model

### Prompt Injection via WhatsApp

**Threat:** User sends a crafted message trying to make the agent execute system commands or leak data.

**Mitigations:**
- Tool deny list blocks `bash`, `file_write`, `file_edit`
- Agent only has access to 8 specific MCP tools (mandi, weather, etc.)
- MCP servers only call data.gov.in and Bhashini APIs — no local system access
- Structured error responses prevent information leakage

### Unauthorized Access

**Threat:** Unknown phone numbers send messages to the bot.

**Mitigations:**
- `allowFrom` whitelist (when configured)
- `groupPolicy: disabled` prevents group-based abuse
- Localhost gateway prevents direct API access

### API Key Leakage

**Threat:** API keys exposed in config files or logs.

**Mitigations:**
- All keys via `${ENV_VAR}` references
- No plaintext secrets in any config file
- Docker containers use environment variable passing

### Denial of Service

**Threat:** Flood of messages exhausting API quotas or compute.

**Mitigations:**
- data.gov.in has built-in rate limiting
- TTL caching reduces API calls (6h for mandi, 3h for weather)
- WhatsApp's own rate limiting on the platform level
- `allowFrom` restricts to known numbers

## Configuration Checklist

Before deploying:

- [ ] Set all environment variables in `.env` or deployment platform
- [ ] Configure `allowFrom` with authorized phone numbers
- [ ] Verify `gateway.bind: localhost` is set
- [ ] Verify `tools.deny` includes `bash`, `computer`, `file_write`, `file_edit`
- [ ] Verify `groupPolicy: disabled`
- [ ] Test: send message from unauthorized number → should be rejected
- [ ] Test: agent tries to use denied tool → should be blocked
- [ ] Review Docker container settings (read-only, no-new-privileges)
