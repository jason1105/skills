# CI / Pages 怪癖

> 从 SKILL.md 拆出，内容为实测口径原样搬运。触发：写 `.gitlab-ci.yml`、配 Pages、定时流水线与 masked 变量。

## git.tsintergy.com GitLab 13.11 CI/Pages quirks (verified 2026-08-17)

- **No `publish:` keyword** (added in GitLab 17.10) — pipelines fail
  validation with `jobs:pages config contains unknown keys: publish`. On
  13.x, Pages publishing is implicit: the job MUST be named `pages` and its
  artifact must contain a `public/` dir.
- **Runner tags must match an existing runner.** A job with `tags:
  [docker]` hangs `pending` forever (no such tagged runner; the project
  runner `test` is untagged). Known-good tags on this instance (from
  `lvwei/trending`): `tsintergy-public` (build/test) and `pages-share`
  (Pages publish). List runners: `glab api "runners?type=project_type"`.
- Working Pages pattern (two jobs): build job (`tags: [tsintergy-public]`,
  `image: python:3.12-slim`, `artifacts: paths: [public]`) → `pages` job
  (`tags: [pages-share]`, `image: alpine:latest`, `needs: [build]`,
  re-declares `artifacts: paths: [public]`).
- Scheduled pipelines + masked CI variables via API:
  `glab api -X POST projects/<id>/pipeline_schedules -f description=...
  -f ref=master -f 'cron=0 * * * *' -f cron_timezone=Asia/Shanghai`;
  `glab api -X POST projects/<id>/variables -f key=LLM_API_KEY
  -f value=<key> -f masked=true`.
- Private projects: the Pages URL 302s to sign-in for anonymous curl —
  EXPECTED (auth required), not a broken deploy. Verify via pipeline job
  status instead. Example deployed project: `lvwei/llm-monitor` (hourly
  probe → Pages).
