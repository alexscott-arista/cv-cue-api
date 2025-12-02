# CloudVision CUE CLI Usage Guide

The cv-cue-api cli tool provides a Docker-like command-line interface with hierarchical subcommands.

## Command Structure

```
cv-cue-api [GLOBAL OPTIONS] COMMAND [SUBCOMMAND] [OPTIONS]
```

## Global Options

- `-v, --verbose` - Enable verbose output

## Session Commands

### Login
Create a new session with the CV-CUE API:

```bash
cv-cue-api session login
```

### Check Session Status
Check if your current session is active:

```bash
cv-cue-api session status
```

### Clear Session Cache
Clear the cached session file:

```bash
cv-cue-api session clear
```

## Managed Devices Commands

### List Access Points

Basic usage:
```bash
cv-cue-api managed-devices list-aps
```

With pagination:
```bash
cv-cue-api managed-devices list-aps --pagesize 50 --startindex 100
```

With simple filters:
```bash
cv-cue-api managed-devices list-aps --active true --model AP-555
```

With multiple values for same filter:
```bash
cv-cue-api managed-devices list-aps --model AP-555 --model AP-635
```

With advanced filters:
```bash
cv-cue-api managed-devices list-aps \
  --filter name:contains:Arista \
  --filter name:contains:5D:BF \
  --filter-operator AND
```

Available filter operators:
- `equals` - Exact match
- `contains` - Contains substring
- `notContains` - Does not contain substring
- `greaterThan` - Greater than (>)
- `lessThan` - Less than (<)
- `greaterThanOrEquals` - Greater than or equals (>=)
- `lessThanOrEquals` - Less than or equals (<=)
- `notEquals` - Not equal (!=)

Table output format:
```bash
cv-cue-api managed-devices list-aps --output table --pagesize 20
```

Compact output (just names and MACs):
```bash
cv-cue-api managed-devices list-aps --output compact
```

With total count:
```bash
cv-cue-api managed-devices list-aps --total-count --output table
```

Sorting:
```bash
cv-cue-api managed-devices list-aps --sortby name --descending
```

### Get All Access Points

Fetch all devices across all pages:
```bash
cv-cue-api managed-devices get-all-aps
```

Just get the count:
```bash
cv-cue-api managed-devices get-all-aps --output count
```

With filters:
```bash
cv-cue-api managed-devices get-all-aps \
  --filter name:contains:AP \
  --active true \
  --output count
```

## Complete Examples

### Example 1: Login and list devices in table format
```bash
cv-cue-api session login
cv-cue-api managed-devices list-aps --output table --pagesize 10
```

### Example 2: Find all Arista devices with specific model
```bash
cv-cue-api managed-devices list-aps \
  --filter name:contains:Arista \
  --model AP-555 \
  --output table \
  --total-count
```

### Example 3: Get total count of active devices
```bash
cv-cue-api managed-devices get-all-aps --active true --output count
```

### Example 4: Complex filtering with multiple conditions
```bash
cv-cue-api managed-devices list-aps \
  --filter name:contains:Test \
  --filter active:equals:true \
  --filter-operator AND \
  --sortby name \
  --output table
```

### Example 5: Verbose mode for debugging
```bash
cv-cue-api -v managed-devices list-aps --pagesize 5
```

## Environment Variables

The CLI requires these environment variables to be set:

- `CV_CUE_KEY_ID` - Your CV-CUE API key ID
- `CV_CUE_KEY_VALUE` - Your CV-CUE API key value
- `CV_CUE_CLIENT_ID` - Client identifier
- `CV_CUE_BASE_URL` - Base URL for the API (optional)

Example `.env` file:
```bash
CV_CUE_KEY_ID="KEY-1234"
CV_CUE_KEY_VALUE="abcd1234"
CV_CUE_CLIENT_ID="Eaxmple Key"
CV_CUE_BASE_URL="https://wifi.arista.com/wifi/api/"
```

## Session Management

The CLI automatically manages sessions:
- Sessions are cached in `.session` file
- Commands automatically login if session is expired
- Use `session status` to check current session
- Use `session clear` to force re-authentication

## Output Formats

### JSON (default)
Returns the raw API response as JSON. Useful for scripting and piping to `jq`.

### Table
Human-readable table format showing key device information.

### Compact
One line per device showing name and MAC address only.

### Count (get-all-aps only)
Just shows the total number of devices.
