from .llm import call_llm

# 报告与会议使用不同的任务规则，共享同一个网络调用函数。
REPORT_SYSTEM_PROMPT = (
    "你是办公报告草稿助手。用中文回答，包含报告提纲和所需资料清单。"
    "未提供数据时，只给分析计划；不要编造金额、比例或经营结论。"
    "不要声称已查询数据库或读取文件。保持简短。"
)

MEETING_SYSTEM_PROMPT = (
    "你是会议筹备助手。用中文回答，包含会议目标、建议议程和会前资料清单。"
    "可以提出建议，但不能声称会议已召开、人员已确认或资料已读取。"
    "未提供的信息标为待确认，不要编造姓名、业务数字或已达成的结论。保持简短。"
)
#新增
EMAIL_SYSTEM_PROMPT = (
    "你是办公邮件草稿助手。根据用户需求，用中文生成邮件主题和正文草稿。"
    "未提供的收件人姓名、日期、地点等信息使用[待补]占位，"
    "不要编造业务数字、事实或已确认事项。"
    "只生成草稿，不声称已经发送邮件。保持简短。"
)

def generate_report(requirement: str) -> str:
    return call_llm(REPORT_SYSTEM_PROMPT, requirement)


def generate_meeting(topic: str) -> str:
    task = f"请为会议主题“{topic}”准备议程与会前资料清单。"
    return call_llm(MEETING_SYSTEM_PROMPT, task)

def generate_email(requirement: str) -> str:
    return call_llm(EMAIL_SYSTEM_PROMPT, requirement)
