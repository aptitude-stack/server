# Log Ingestion Failures

## Symptoms

- Grafana logs panels are empty
- Loki is reachable but queries return no application logs
- Promtail is down or showing scrape errors
- A known `X-Request-ID` does not appear in Loki after a request

## Checks

1. Confirm the observability profile is running with `docker compose --profile observability ps`.
2. Probe Loki directly: `curl http://127.0.0.1:3100/ready`.
3. Probe Promtail metrics: `curl http://127.0.0.1:9080/metrics`.
4. Hit the API with a known request ID:

   ```bash
   curl -H 'X-Request-ID: runbook-loki-check' http://127.0.0.1:8000/healthz
   ```

5. Query Loki for that value:

   ```bash
   curl --get \
     --data-urlencode 'query={service="server"} |= "runbook-loki-check"' \
     http://127.0.0.1:3100/loki/api/v1/query
   ```

## Actions

1. If Promtail is down, restart the observability stack and re-check the shared `aptitude-logs` volume mounts on `server` and `promtail`.
2. If Loki is down, restart `loki` and verify its local data/config mounts are present.
3. If the API is healthy but no logs arrive, confirm `LOG_FILE_PATH=/var/log/aptitude/app.jsonl` is set on the `server` container.
4. If the file sink exists but Loki queries stay empty, inspect Promtail metrics and logs for push failures against `http://loki:3100/loki/api/v1/push`.
5. Use the same `X-Request-ID` across API probes, Grafana searches, and audit lookups to confirm whether the failure is in logging, shipping, or persistence correlation.
