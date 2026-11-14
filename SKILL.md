---
name: job-hunter
description: Chinese job search assistant for Hangzhou. Analyzes Chinese job listings, matches them against the user's resume, scores job fit, generates BOSS直聘 communication messages, and tracks applications.
  Triggers: /job-hunt, "find jobs", "job search", "hunt for jobs"
---

# Job Hunter Skill

Automates your job search: scrapes LinkedIn, Indeed, and 100+ job boards daily, scores every posting against your resume, and saves a ranked tracker to Obsidian. No LinkedIn account needed.

## Quick Start

### First-Time Setup

1. **Set up virtual environment:**
   ```bash
   bash ~/.claude/skills/job-hunter/scripts/setup_venv.sh
   ```

2. **Configure preferences:**
   ```bash
   ~/.venv/job-hunter/bin/python3 ~/.claude/skills/job-hunter/scripts/setup_config.py
   ```

3. **Set your resume path** (PDF, DOCX, or TXT)

4. **Set Obsidian vault path**

### Usage

Run the job hunt:
```
/job-hunt
```

Or with specific options:
```
/job-hunt --keywords "software engineer" --location "San Francisco"
```

## How It Works

Two complementary providers run on a smart schedule:

| Provider | Source | Cost | Schedule |
|----------|--------|------|----------|
| **JobSpy** | LinkedIn guest API + Indeed | Free, no key | Every day |
| **JSearch** | Google Jobs aggregator (100+ boards) | 200 req/month free | Every 2 days |

On days both run, results are merged and deduplicated. On off-days, JobSpy runs alone.

## Workflow

When invoked, the skill executes these steps:

### 1. Load Configuration
- Read config from `~/.config/job-hunter/config.json`
- Validate paths and optional API keys

### 2. Read Resume
- Load resume from configured path
- Extract key skills for matching

### 3. Search Jobs — JobSpy (daily) + JSearch (every 2 days)

**JobSpy** hits LinkedIn's undocumented public guest API — no login, no API key, returns full job descriptions (~60 results/run).

**JSearch** queries Google Jobs via RapidAPI, aggregating postings from LinkedIn, Indeed, Dice, Remotive, and 100+ company career pages (~100 results/run).

The scheduler uses a state file (`~/.job-hunter-jsearch-last-run`) to decide whether JSearch runs. If both run, their outputs are merged and deduplicated:

```
JobSpy  ~60 jobs ─┐
                  ├─ deduplicate → ~130–160 unique jobs
JSearch ~100 jobs─┘
```

### 4. Score against resume

Each job is scored 0–100 based on skill keyword matching:
- +5 per skill match (Python, SQL, machine learning, etc.)
- Bonus: role alignment (+15), healthcare domain (+10), EHR tools (+8), remote (+5)
- Skills are extracted automatically from your resume (PDF/DOCX/TXT)

### 4b. AI Re-rank (interactive runs only)

Keyword scoring is literal — it can't distinguish "we use Python for Excel macros" from "ML platform team". When the skill runs interactively (not via cron), Claude re-ranks the top jobs by actually reading them:

1. **Prep** — build a compact packet of the top ~30 keyword-scored jobs + resume:
   ```bash
   ~/.venv/job-hunter/bin/python3 ~/.claude/skills/job-hunter/scripts/rerank.py prep \
     -i /tmp/scored.json -o /tmp/rerank_packet.md --top 30
   ```
2. **Judge** — Claude reads `/tmp/rerank_packet.md` and scores every job 0–100 for holistic fit (seniority, domain, day-to-day work vs. resume — not keyword counts). Claude writes the result to `/tmp/rerank_scores.json` as:
   ```json
   {"<job id>": {"ai_score": 88, "ai_reason": "Strong healthcare + Python overlap"}}
   ```
   Every job id from the packet must appear. Keep reasons under 80 chars.
3. **Apply** — merge scores back and re-sort:
   ```bash
   ~/.venv/job-hunter/bin/python3 ~/.claude/skills/job-hunter/scripts/rerank.py apply \
     -i /tmp/scored.json -r /tmp/rerank_scores.json
   ```

Each job gains `final_score` (AI score when present, keyword score otherwise) and the tracker sorts/filters by it, adding a **Why** column. Cron runs skip this step automatically — `write_tracker.py` falls back to keyword scores.

### 5. Save Job Tracker to Obsidian

Writes `Job Tracker - YYYY-MM-DD.md` with all jobs scoring **> 70**, sorted by score descending. Idempotent — skips if today's file already exists.

```markdown
# 杭州国内求职助手

这是一个专门面向中国国内招聘市场的 AI 求职助手。

主要服务于杭州地区的求职者，帮助用户收集招聘信息、分析岗位要求、匹配个人简历、评估岗位价值，并生成求职沟通话术。

## 求职目标

- 工作城市：杭州
- 目标薪资：税前 12K-18K
- 工作经验：3-5年及以上
- 目标行业：快消品、消费品、电商、互联网、品牌营销

## 目标岗位

- 小红书运营
- 小红书PR
- 达人营销
- 品牌营销
- 内容营销
- 新媒体运营

## 用户核心优势

- 4年小红书PR经验
- 2年抖音商务及内容经验
- 快消品品牌从0到1经验
- 达人投放ROI达到8-9
- 百万阅读内容爆文经验
- 独立负责品牌推广及内容运营

## 核心工作流程

1. 接收用户提供的国内招聘岗位信息。
2. 提取公司、岗位、薪资、地点和任职要求。
3. 分析岗位与用户简历的匹配程度。
4. 输出0-100分的匹配评分及具体原因。
5. 判断薪资、工作内容和发展空间是否符合求职目标。
6. 生成针对岗位的BOSS直聘沟通话术。
7. 记录投递进度和面试结果。

## 招聘数据来源

优先使用用户提供的BOSS直聘、猎聘等招聘岗位链接或导出的岗位数据。

不得将LinkedIn、Indeed的海外岗位结果冒充国内招聘结果。

如果无法获取岗位完整信息，应明确提示用户补充，不得编造公司、薪资或招聘要求。

## 岗位分析原则

- 优先考虑与小红书、品牌营销、达人投放相关的岗位。
- 重视实际工作职责，不仅根据岗位名称判断。
- 区分必须具备的技能和加分项。
- 对不符合薪资、工作内容要求的岗位说明原因。
- 不自动投递简历，所有投递行为由用户确认。
```

### 6. Wait for User Selection — STOP HERE

After saving the tracker:

> "Saved X jobs to **Job Tracker - YYYY-MM-DD.md** in Obsidian. Review the file and tell me which numbers you'd like cover letters for (e.g. '1, 3')."

**Never auto-generate cover letters. Always wait for user to select.**

### 7. Generate Cover Letters

```bash
~/.venv/job-hunter/bin/python3 ~/.claude/skills/job-hunter/scripts/generate_cover_letters.py \
  --jobs /path/to/scored_jobs.json \
  --indices "1,3"
```

Saves to `Cover Letters/YYYY-MM-DD/Company - Title.md` in your Obsidian vault.

## Configuration Reference

Config file: `~/.config/job-hunter/config.json`

```json
{
  "jsearch_api_key": "your-rapidapi-key",
  "search_provider": "jobspy",
  "resume_path": "/path/to/resume.pdf",
  "obsidian_vault": "~/Documents/Obsidian Vault/job-hunter",
  "user_name": "Your Name",
  "min_score": 70,
  "search": {
    "keywords": ["小红书运营","小红书PR","达人营销","品牌营销","内容营销","新媒体运营"],
    "location": "杭州",
    "remote": true,
    "time_range": "week",
    "max_results_per_query": 20,
    "job_domains": ["linkedin.com", "indeed.com"],
    "linkedin_fetch_description": true,
    "request_delay": 3,
    "proxies": [],
    "user_agent": "",
    "country_indeed": "USA"
  }
}
```

### Key Fields

| Field | Description |
|-------|-------------|
| `jsearch_api_key` | RapidAPI key for JSearch (free tier: 200 req/month) |
| `search_provider` | `"jobspy"` (default) or `"jsearch"` for manual override |
| `min_score` | Tracker only includes jobs scoring above this (default 70) |
| `search.max_results_per_query` | Max 20 for JobSpy, max 10 for JSearch |
| `search.job_domains` | Used by JobSpy; maps to `linkedin`, `indeed`, `glassdoor`, `zip_recruiter`. Glassdoor is off by default (upstream 400 errors) |
| `search.linkedin_fetch_description` | Full LinkedIn descriptions (1 extra request/job). Set `false` if you hit 429 rate limits |
| `search.request_delay` | Seconds between JobSpy calls (default 3) — reduces rate-limiting |
| `search.proxies` | Proxy list `["user:pass@host:port"]` — JobSpy round-robins through them; the reliable fix for persistent LinkedIn 429s |
| `search.user_agent` | Override JobSpy's default browser user-agent if it gets blocked |
| `search.country_indeed` | Indeed/Glassdoor country (default `"USA"`) |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/jobspy_scraper.py` | LinkedIn/Indeed via guest API (no key) |
| `scripts/jsearch_scraper.py` | Google Jobs via RapidAPI |
| `scripts/run_search.py` | Provider-switching search CLI |
| `scripts/score_jobs.py` | Score jobs against resume (keyword-based) |
| `scripts/rerank.py` | Prep/apply AI re-ranking by Claude (interactive runs) |
| `scripts/generate_cover_letters.py` | Generate cover letter templates |
| `scripts/write_tracker.py` | Write ranked Job Tracker markdown to Obsidian |
| `scripts/daily_job_hunt.sh` | Full pipeline orchestration (cron) |
| `scripts/setup_config.py` | Interactive config setup |
| `scripts/setup_venv.sh` | Virtual environment setup |
| `scripts/common/` | Shared modules (config, scoring, dedup) |

## Obsidian Structure

```
job-hunter/
├── Job Tracker - 2026-02-28.md   # Today's tracker
├── Job Tracker - 2026-02-27.md   # Yesterday's tracker
├── Cover Letters/
│   ├── 2026-02-28/
│   │   ├── Dana-Farber - Data Engineer II.md
│   │   └── Veeva Systems - Senior Health Data Informaticist.md
│   └── 2026-02-27/
```

## Scheduling

Set up a daily cron to run the full pipeline automatically:

```bash
# Run job hunt daily at 10am
0 10 * * * bash ~/.claude/skills/job-hunter/scripts/daily_job_hunt.sh
```

The script decides internally whether to also run JSearch (every 2 days). To force a JSearch run:

```bash
rm ~/.job-hunter-jsearch-last-run
```

## API Usage & Cost

| Provider | Free Tier | Usage per run | Monthly (daily cron) |
|----------|-----------|---------------|----------------------|
| JobSpy | Unlimited | 0 requests | $0 |
| JSearch | 200 req/month | 7–14 requests | ~98 req/month ✓ |

## Troubleshooting

**No jobs found**
- Check `~/.job-hunter.log` — the run now prints per-site totals (`Per-site totals: linkedin=0, indeed=25`) so you can see which board failed
- Broaden search keywords in config
- Each site is scraped independently, so one board failing no longer wipes out the others' results

**LinkedIn returns 0 results / 429 errors**
- LinkedIn aggressively rate-limits (~100 results per IP, then blocks). In config:
  1. Set `search.linkedin_fetch_description: false` (biggest win — cuts requests by ~95%)
  2. Lower `search.max_results_per_query`
  3. Increase `search.request_delay` (e.g. 10)
  4. Add `search.proxies` — per JobSpy maintainers, proxies are the only durable fix
- Indeed has no rate limiting and full descriptions — results still flow while LinkedIn cools down (blocks typically clear within hours)

**JSearch API errors**
- Verify key at [rapidapi.com](https://rapidapi.com)
- Check monthly usage (200 free requests)
- Delete `~/.job-hunter-jsearch-last-run` to retry

**Glassdoor 400 errors in logs**
- Known upstream issue in JobSpy — Glassdoor is now excluded from default sites; remove `glassdoor.com` from `job_domains` if you added it

**Virtual environment issues**
- Re-run `bash ~/.claude/skills/job-hunter/scripts/setup_venv.sh`
- Requires Python 3.10+
