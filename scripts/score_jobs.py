
"""China-market job scoring for Xiaohongshu / brand marketing roles."""

ROLE_GROUPS = {
    "小红书运营": [
        "小红书运营", "小红书内容运营", "小红书种草",
        "小红书营销", "小红书推广", "小红书投放",
    ],
    "PR及媒介": [
        "小红书pr", "媒介pr", "媒介投放", "达人投放",
        "达人营销", "达人商务", "kol", "koc",
        "博主合作", "达人资源",
    ],
    "品牌营销": [
        "品牌营销", "品牌推广", "品牌策划",
        "整合营销", "品牌传播", "市场营销",
    ],
    "内容营销": [
        "内容营销", "内容策划", "内容运营",
        "内容推广", "爆款内容", "短视频运营",
    ],
    "新媒体运营": [
        "新媒体运营", "社交媒体运营", "社媒运营",
        "抖音运营", "公众号运营",
    ],
}

SKILL_GROUPS = {
    "达人投放": ["达人投放", "kol投放", "koc投放", "达人合作"],
    "媒介资源": ["媒介资源", "达人资源", "博主资源", "kol资源"],
    "内容策划": ["内容策划", "选题策划", "脚本策划", "创意策划"],
    "数据分析": ["数据分析", "投放复盘", "roi", "转化率"],
    "商务合作": ["商务合作", "商务bd", "商务谈判", "品牌合作"],
    "账号运营": ["账号运营", "矩阵运营", "内容运营"],
    "投流能力": ["千川", "信息流投放", "广告投放", "付费推广"],
    "爆款打造": ["爆款打造", "爆文", "百万阅读", "内容增长"],
}

INDUSTRY_TERMS = [
    "快消", "消费品", "美妆", "食品", "饮料",
    "日用品", "电商", "品牌方", "消费品牌",
]

EXCLUDE_TERMS = [
    "纯电话销售", "保险销售", "房产销售",
    "客服专员", "售后客服",
]


def score_job(job, resume_skills=None):
    title = str(job.get("title", "")).lower()
    description = str(job.get("description", "")).lower()
    text = title + " " + description

    matched_roles = []
    for role, terms in ROLE_GROUPS.items():
        if any(term.lower() in title for term in terms):
            matched_roles.append(role)

    if not matched_roles:
        for role, terms in ROLE_GROUPS.items():
            if any(term.lower() in text for term in terms):
                matched_roles.append(role)

    role_score = min(40, len(matched_roles) * 20)

    matched_skills = []
    for skill, terms in SKILL_GROUPS.items():
        if any(term.lower() in text for term in terms):
            matched_skills.append(skill)

    skill_score = min(30, len(matched_skills) * 6)

    industry_score = 15 if any(
        term in text for term in INDUSTRY_TERMS
    ) else 0

    seniority_terms = ["3-5年", "3年以上", "5年以上", "资深", "高级"]
    seniority_score = 10 if any(
        term in text for term in seniority_terms
    ) else 5

    salary = str(job.get("salary", ""))
    salary_score = 5 if salary else 0

    total = min(
        100,
        role_score + skill_score + industry_score
        + seniority_score + salary_score
    )

    excluded = [term for term in EXCLUDE_TERMS if term in text]

    reasons = []
    if matched_roles:
        reasons.append("岗位方向：" + "、".join(matched_roles))
    if matched_skills:
        reasons.append("技能：" + "、".join(matched_skills))
    if industry_score:
        reasons.append("有消费品行业相关经验要求")
    if excluded:
        reasons.append("需人工确认：包含" + "、".join(excluded))

    reason = "；".join(reasons) if reasons else "暂未发现明显匹配点"

    return total, reason


def score_jobs(jobs, resume_skills=None, resume_path=None):
    for job in jobs:
        score, reason = score_job(job, resume_skills)
        job["match_score"] = score
        job["match_reason"] = reason

    jobs.sort(key=lambda x: x["match_score"], reverse=True)
    return jobs
