# -*- coding: utf-8 -*-
"""
Email template module for Recruitment Agent.
Provides: get_templates(), get_template(template_id), fill_template(template_id, placeholders)
"""

TEMPLATES = {
    "interview_invitation": {
        "name": "面试邀请",
        "subject": "面试邀请 - {company} - {position}",
        "body": """尊敬的 {candidate_name}，

您好！

感谢您申请 {company} 的 {position} 职位。经过初步筛选，我们希望邀请您参加面试。

面试信息：
- 时间：{interview_time}
- 地点：{interview_location}
- 面试官：{interviewer}

请回复确认是否准时参加。如有任何问题，请随时联系我们。

此致
{company} 人力资源部
{contact_email}
"""
    },
    "offer_letter": {
        "name": "Offer 发放",
        "subject": "Offer Letter - {position} - {company}",
        "body": """尊敬的 {candidate_name}，

您好！

我们很高兴地通知您，您已成功通过 {company} 的面试流程，我们正式向您发出 {position} 职位的 Offer。

Offer 要点：
- 职位：{position}
- 薪资：{salary}
- 入职日期：{start_date}
- 工作地点：{location}

请在 {deadline} 前确认接受 Offer，并按照附件中的入职指南准备材料。

如有任何问题，请随时联系我们。

此致
{company} 人力资源部
{contact_email}
"""
    },
    "rejection": {
        "name": "感谢信（未通过）",
        "subject": "感谢您关注 {company} - {position} 职位",
        "body": """尊敬的 {candidate_name}，

您好！

感谢您申请 {company} 的 {position} 职位，并对您的关注和努力表示衷心的感谢。

经过慎重评估，我们遗憾地通知您，本次未能进入下一轮。但请您相信，这是因为当前职位与您背景的匹配度并非最佳，而非您不够优秀。

我们会将您的简历保存在人才库中，未来如有更匹配的职位，我们会第一时间与您联系。

再次感谢您的理解与支持，祝您职业发展顺利！

此致
{company} 人力资源部
{contact_email}
"""
    }
}


def get_templates():
    """Get all templates."""
    return TEMPLATES


def get_template(template_id):
    """Get a specific template by ID."""
    return TEMPLATES.get(template_id)


def fill_template(template_id, placeholders):
    """
    Fill a template with placeholders.
    Args:
        template_id: Template ID (e.g., "interview_invitation")
        placeholders: dict of placeholder values (e.g., {"candidate_name": "John", "company": "ACME"})
    Returns:
        dict with "subject" and "body" (filled)
    """
    template = TEMPLATES.get(template_id)
    if not template:
        return None
    
    subject = template["subject"].format(**placeholders)
    body = template["body"].format(**placeholders)
    
    return {"subject": subject, "body": body}
