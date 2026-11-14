
#!/usr/bin/env python3
"""Import and score manually collected China job listings."""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common.job_scoring import score_jobs

REQUIRED_FIELDS = [
    "title", "company", "location", "salary",
    "description", "url", "source"
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="scored_jobs.csv")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser()
    output_path = Path(args.output).expanduser()

    if not input_path.exists():
        print(f"找不到文件：{input_path}")
        sys.exit(1)

    with input_path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as f:
        reader = csv.DictReader(f)

        missing = set(REQUIRED_FIELDS) - set(reader.fieldnames or [])
        if missing:
            print("CSV 缺少字段：" + ", ".join(sorted(missing)))
            sys.exit(1)

        jobs = list(reader)

    if not jobs:
        print("没有读取到岗位，请检查 CSV 文件。")
        sys.exit(1)

    scored = score_jobs(jobs)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = REQUIRED_FIELDS + ["match_score", "match_reason"]

    with output_path.open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(scored)

    print(f"成功分析 {len(scored)} 个岗位")
    print(f"结果保存位置：{output_path}")

    for index, job in enumerate(scored, 1):
        print(
            f"{index}. {job['title']} | {job['company']} "
            f"| {job['match_score']}分"
        )


if __name__ == "__main__":
    main()

