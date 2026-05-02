---
name: sonarcloud-api-navigation
description: Fetches vulnerability findings and their source code context from SonarCloud API. Use this skill at the start of any exploitation workflow to gather all data needed to craft exploits. Returns clean JSON containing finding metadata (rule, line, severity), data flow trace, and the actual source code around each vulnerability sink.
---

# SonarCloud API Navigation

## Purpose

Extract everything needed to exploit a vulnerability:
1. Finding metadata - what type of vuln, where, severity
2. Data flow - how user input reaches the dangerous sink
3. Source code context - the actual vulnerable code

This skill is the first step in the exploitation workflow.

## Required Environment

The following environment variables must be set before using this skill:

- SONAR_TOKEN: SonarCloud authentication token
- SONAR_PROJECT_KEY: Project key (e.g., abdellah0x0_agentic-devsecops-pipeline)
- SONAR_HOST: https://sonarcloud.io

## Step 1 - Fetch All Vulnerabilities

Use this curl command to retrieve all vulnerability findings:

```
curl -s -u "${SONAR_TOKEN}:" "${SONAR_HOST}/api/issues/search?componentKeys=${SONAR_PROJECT_KEY}&types=VULNERABILITY&ps=100"
```

Extract these fields from the response (per issue):

| Field | Path in JSON | Use for |
|-------|-------------|---------|
| key | issues[].key | Unique ID |
| rule | issues[].rule | Vuln type (e.g., jssecurity:S3649) |
| severity | issues[].severity | Priority |
| component | issues[].component | File path |
| line | issues[].line | Sink location |
| message | issues[].message | SonarCloud description |
| flows | issues[].flows[0].locations | Data flow trace |

Quick extraction with jq:

```
curl -s -u "${SONAR_TOKEN}:" "${SONAR_HOST}/api/issues/search?componentKeys=${SONAR_PROJECT_KEY}&types=VULNERABILITY&ps=100" | jq '.issues[] | {key, rule, severity, component, line, message}'
```

## Step 2 - Parse Data Flow

The flows field is the most valuable data. Structure:

- flows[0].locations[] is an array of taint locations
- First element = SINK (where the dangerous call happens)
- Middle elements = PROPAGATION (how taint flows through code)
- Last element = SOURCE (where user input enters the application)

Key fields to extract:

- source_line = flows[0].locations[-1].textRange.startLine
- sink_line = flows[0].locations[0].textRange.startLine
- source_msg = flows[0].locations[-1].msg
- sink_msg = flows[0].locations[0].msg

Extract using jq:

```
jq '.issues[0].flows[0].locations[0] | {line: .textRange.startLine, msg}'
jq '.issues[0].flows[0].locations[-1] | {line: .textRange.startLine, msg}'
jq '.issues[0].flows[0].locations[1:-1] | map({line: .textRange.startLine, msg})'
```

## Step 3 - Fetch Source Code Around Sink

For each finding, get plus or minus 10 lines around the sink:

```
COMPONENT="${SONAR_PROJECT_KEY}:app/server.js"
SINK_LINE=52
FROM=$((SINK_LINE - 10))
TO=$((SINK_LINE + 10))

curl -s -u "${SONAR_TOKEN}:" "${SONAR_HOST}/api/sources/show?key=${COMPONENT}&from=${FROM}&to=${TO}"
```

The response contains HTML-formatted code. Strip the HTML to get clean source:

```
curl -s -u "${SONAR_TOKEN}:" "${URL}" | jq -r '.sources[] | "\(.line)\t\(.code)"' | sed 's/<[^>]*>//g' | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g'
```

This produces clean, line-numbered source code ready for analysis.

## Output Format

After processing all findings, return exactly this JSON structure:

```
{
  "skill": "sonarcloud-api-navigation",
  "status": "success",
  "findings_count": 4,
  "findings": [
    {
      "finding_key": "AZ3kDGPvBhuZ9C0LAN0b",
      "rule_id": "jssecurity:S3649",
      "severity": "BLOCKER",
      "file": "app/server.js",
      "sink_line": 52,
      "source_line": 49,
      "message": "Change this code to not construct SQL queries directly from user-controlled data",
      "data_flow": {
        "source": "user can craft an HTTP request with malicious content",
        "sink": "this invocation is not safe; a malicious value can be used as argument",
        "propagation_steps": [
          "field username assigned malicious value",
          "concatenation propagates malicious content to query"
        ]
      },
      "code_context": {
        "from_line": 42,
        "to_line": 62,
        "code": "Line-numbered source code here, HTML stripped"
      }
    }
  ]
}
```

## Workflow Summary

1. GET /api/issues/search to retrieve all findings
2. For each finding:
   - Extract metadata (rule, line, severity)
   - Parse data flow (source to sink)
   - GET /api/sources/show to fetch source code
   - Clean HTML from code
3. Return structured JSON

## Critical Rules

1. Always run this skill FIRST before any exploitation logic
2. Strip HTML from /api/sources/show responses using sed and jq
3. Include line numbers in code context for accurate sink reference
4. Return JSON only - no narrative text in the final response

## Anti-Patterns

- Do not fetch the entire file - use from and to parameters
- Do not skip the flows field - it explains the vulnerability path
- Do not return HTML-encoded code to downstream skills
- Do not combine this with exploitation logic - keep single responsibility

## Example Full Workflow

```
# 1. Set environment
export SONAR_TOKEN="your_token"
export SONAR_PROJECT_KEY="abdellah0x0_agentic-devsecops-pipeline"
export SONAR_HOST="https://sonarcloud.io"

# 2. Fetch all findings
FINDINGS=$(curl -s -u "${SONAR_TOKEN}:" "${SONAR_HOST}/api/issues/search?componentKeys=${SONAR_PROJECT_KEY}&types=VULNERABILITY&ps=100")

# 3. Loop through findings
echo "$FINDINGS" | jq -c '.issues[]' | while read -r issue; do
  KEY=$(echo "$issue" | jq -r '.key')
  RULE=$(echo "$issue" | jq -r '.rule')
  COMPONENT=$(echo "$issue" | jq -r '.component')
  SINK_LINE=$(echo "$issue" | jq -r '.line')
  
  # 4. Fetch source code around sink
  FROM=$((SINK_LINE - 10))
  TO=$((SINK_LINE + 10))
  
  CODE=$(curl -s -u "${SONAR_TOKEN}:" "${SONAR_HOST}/api/sources/show?key=${COMPONENT}&from=${FROM}&to=${TO}" | jq -r '.sources[] | "\(.line)\t\(.code)"' | sed 's/<[^>]*>//g')
  
  echo "Finding: $KEY ($RULE) at line $SINK_LINE"
  echo "$CODE"
done
```