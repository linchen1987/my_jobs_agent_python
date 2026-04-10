import os
from dotenv import load_dotenv
from notify.telegram import notify_jobs

load_dotenv()

mock_jobs = [
    {
        "original_data": {
            "list_metadata": {
                "url": "https://eleduck.com/tposts/gYfZOZ",
                "id": "gYfZOZ",
                "title": "【免费推荐/全职远程】US$4000-5000/偏后端全栈开发/加州技术公司",
            }
        },
        "llm_analysis": {
            "extracted_info": {
                "company_introduction": "位于美国加州的技术公司，服务于多元化的家族办公室及其旗下投资组合公司。业务涵盖AI自动化、智能零售、房地产债务以及内部AI工具开发。",
                "skill_requirements": "1. 3年以上全栈开发经验（偏后端/数据）；2. 精通 Python 及数据处理（Pandas、NumPy、ETL）；3. 熟悉 PostgreSQL；4. 熟悉至少一种前端框架（React/Next.js、Vue）；5. 有 LLM 应用开发经验。",
                "salary_benefits": "月薪 USD $4,000–5,000（年度总包 $52K–65K）；根据表现有年终奖及业绩分红；全远程，异步优先。",
            },
            "analysis": {"reasoning": "远程全职开发岗，月薪$4000起，属长期开发工作"},
        },
    },
    {
        "original_data": {
            "list_metadata": {
                "url": "https://eleduck.com/posts/qzfdLq",
                "id": "qzfdLq",
                "title": "Senior AI Video Engineer｜AI 陪伴平台｜全远程｜美国公司",
            }
        },
        "llm_analysis": {
            "extracted_info": {
                "company_introduction": "硅谷AI陪伴产品科技公司，核心产品为AI互动平台，日活超10万，技术栈覆盖视频生成、流媒体及大模型推理。",
                "skill_requirements": "1. 5年以上AI/ML工程经验，熟练掌握PyTorch；2. 熟悉GPU推理优化（TensorRT, xformers）；3. 具备Python和Node.js开发能力。",
                "salary_benefits": "面议（参考市场水平），全远程办公，灵活工时，项目奖金与绩效激励。",
            },
            "analysis": {"reasoning": "满足开发、长期、远程要求，薪资面议"},
        },
    },
]

if __name__ == "__main__":
    print("发送 Telegram 测试通知...")
    ok = notify_jobs(mock_jobs)
    print("✅ 发送成功" if ok else "❌ 发送失败")
