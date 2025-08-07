import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict, Any, Tuple

from tools.fetch_and_parse_all import fetch_and_parse_all
# from tools.config import source_list
from tools.llm_doubao import DoubaoChat
from tools.analyze_data import analyze_job_with_llm

# 加载环境变量
load_dotenv()

source_list: list[str] = [
    "https://svc.eleduck.com/api/v1/posts?page=1"
]
OFFSET = 0
LIMIT = 0

# 配置日志
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def save_notifications(new_qualified_jobs: List[Dict[str, Any]]) -> None:
    """
    保存新的符合条件的职位到通知文件
    
    Args:
        new_qualified_jobs: 新的符合条件的职位列表
    """
    if not new_qualified_jobs:
        return
    
    notifications_path = ".data/jobs_notifications.md"
    
    # 生成新通知的Markdown内容
    new_notification_content = create_notification_markdown(new_qualified_jobs)
    
    # 加载现有通知内容
    existing_content = ""
    if os.path.exists(notifications_path):
        try:
            with open(notifications_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
        except Exception as e:
            print(f"⚠️ 加载现有通知失败: {e}")
            existing_content = ""
    
    # 合并内容：新通知在前面
    if existing_content:
        all_content = new_notification_content + "\n---\n\n" + existing_content
    else:
        all_content = new_notification_content
    
    # 保存通知文件
    try:
        with open(notifications_path, "w", encoding="utf-8") as f:
            f.write(all_content)
        print(f"\n📢 发现 {len(new_qualified_jobs)} 个新职位，已保存到 {notifications_path}")
    except Exception as e:
        print(f"❌ 保存通知失败: {e}")


def create_notification_markdown(qualified_jobs: List[Dict[str, Any]]) -> str:
    """
    创建新职位通知的Markdown内容
    
    Args:
        qualified_jobs: 符合条件的职位列表
        
    Returns:
        str: 格式化的Markdown通知内容
    """
    if not qualified_jobs:
        return ""
    
    # 获取当前时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 创建通知内容
    markdown = f"# 新职位通知 - {current_time}\n\n"
    markdown += f"发现 {len(qualified_jobs)} 个新的符合条件的招聘信息：\n\n"
    markdown += "| URL | ID | 公司介绍 | 公司网站 | 技能要求 | 薪资待遇 |\n"
    markdown += "|-----|----|---------|---------|---------|---------|\n"
    
    # 添加每行数据
    for job in qualified_jobs:
        original_data = job.get("original_data", {})
        list_metadata = original_data.get("list_metadata", {})
        llm_analysis = job.get("llm_analysis", {})
        extracted_info = llm_analysis.get("extracted_info", {})
        
        # 获取各字段信息
        url = list_metadata.get("url", "")
        job_id = list_metadata.get("id", "")
        company_intro = extracted_info.get("company_introduction", "未提及")
        company_website = extracted_info.get("company_website", "未提及")
        skill_req = extracted_info.get("skill_requirements", "未提及")
        salary = extracted_info.get("salary_benefits", "未提及")
        
        # 清理文本中的换行符和管道符
        def clean_text(text):
            if not text or text == "未提及":
                return "未提及"
            return str(text).replace('\n', ' ').replace('|', '｜').strip()
        
        company_intro = clean_text(company_intro)
        company_website = clean_text(company_website)
        skill_req = clean_text(skill_req)
        salary = clean_text(salary)
        
        # 限制长度避免表格过宽
        def truncate_text(text, max_length=100):
            if len(text) > max_length:
                return text[:max_length] + "..."
            return text
        
        company_intro = truncate_text(company_intro)
        skill_req = truncate_text(skill_req)
        
        markdown += f"| [{job_id}]({url}) | {job_id} | {company_intro} | {company_website} | {skill_req} | {salary} |\n"
    
    return markdown


def create_markdown_table(qualified_jobs: List[Dict[str, Any]]) -> str:
    """
    创建包含合格职位的Markdown表格
    
    Args:
        qualified_jobs: 通过筛选的职位列表
        
    Returns:
        str: 格式化的Markdown表格
    """
    if not qualified_jobs:
        return "## 分析结果\n\n暂无符合条件的招聘信息。\n"
    
    # 创建表格头
    markdown = "## 招聘信息分析结果\n\n"
    markdown += f"共找到 {len(qualified_jobs)} 个符合条件的招聘信息：\n\n"
    markdown += "| URL | ID | 公司介绍 | 公司网站 | 技能要求 | 薪资待遇 |\n"
    markdown += "|-----|----|---------|---------|---------|---------|\n"
    
    # 添加每行数据
    for job in qualified_jobs:
        original_data = job.get("original_data", {})
        list_metadata = original_data.get("list_metadata", {})
        llm_analysis = job.get("llm_analysis", {})
        extracted_info = llm_analysis.get("extracted_info", {})
        
        # 获取各字段信息
        url = list_metadata.get("url", "")
        job_id = list_metadata.get("id", "")
        company_intro = extracted_info.get("company_introduction", "未提及")
        company_website = extracted_info.get("company_website", "未提及")
        skill_req = extracted_info.get("skill_requirements", "未提及")
        salary = extracted_info.get("salary_benefits", "未提及")
        
        # 清理文本中的换行符和管道符
        def clean_text(text):
            if not text or text == "未提及":
                return "未提及"
            return str(text).replace('\n', ' ').replace('|', '｜').strip()
        
        company_intro = clean_text(company_intro)
        company_website = clean_text(company_website)
        skill_req = clean_text(skill_req)
        salary = clean_text(salary)
        
        # 限制长度避免表格过宽
        def truncate_text(text, max_length=100):
            if len(text) > max_length:
                return text[:max_length] + "..."
            return text
        
        company_intro = truncate_text(company_intro)
        skill_req = truncate_text(skill_req)
        
        markdown += f"| [{job_id}]({url}) | {job_id} | {company_intro} | {company_website} | {skill_req} | {salary} |\n"
    
    return markdown


def process_data() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    数据处理函数：负责抓取数据、分析招聘信息
    
    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: 
        (new_analyzed_records, new_qualified_jobs)
    """
    print("=== 开始数据处理阶段 ===\n")
    
    # 初始化LLM客户端
    print("🚀 初始化LLM客户端...")
    llm_client = DoubaoChat()
    
    # 获取所有数据
    print("\n📥 开始抓取数据...")
    all_jobs_data = fetch_and_parse_all(source_list, offset=OFFSET, limit=LIMIT)
    
    if not all_jobs_data:
        print("❌ 没有获取到任何数据")
        return [], []
    
    print(f"\n📊 获取到 {len(all_jobs_data)} 个招聘信息，开始分析...")
    
    # 确保.data目录存在
    os.makedirs(".data", exist_ok=True)
    
    # 加载已分析记录表
    analyzed_jobs = []
    analyzed_json_path = ".data/analyzed_jobs.json"
    if os.path.exists(analyzed_json_path):
        try:
            with open(analyzed_json_path, "r", encoding="utf-8") as f:
                analyzed_jobs = json.load(f)
        except Exception as e:
            print(f"⚠️ 加载已分析记录失败: {e}")
            analyzed_jobs = []
    
    # 创建已分析数据的索引（基于ID）
    analyzed_ids = set()
    for record in analyzed_jobs:
        job_id = record.get("id", "")
        if job_id:
            analyzed_ids.add(job_id)
    
    # 过滤掉已分析过的数据
    unanalyzed_jobs_data = []
    skipped_count = 0
    
    for job_data in all_jobs_data:
        list_metadata = job_data.get("list_metadata", {})
        job_id = list_metadata.get("id", "")
        
        if job_id in analyzed_ids:
            skipped_count += 1
        else:
            unanalyzed_jobs_data.append(job_data)
    
    print(f"📊 过滤结果: 总共 {len(all_jobs_data)} 个招聘信息，跳过 {skipped_count} 个已分析的，需要分析 {len(unanalyzed_jobs_data)} 个新的")
    
    # 分析过滤后的招聘信息
    new_qualified_jobs = []
    new_analyzed_records = []
    current_time = datetime.now().isoformat()
    
    for i, job_data in enumerate(unanalyzed_jobs_data, 1):
        list_metadata = job_data.get("list_metadata", {})
        job_id = list_metadata.get("id", "")
        job_url = list_metadata.get("url", "")
        
        print(f"\n[{i}/{len(unanalyzed_jobs_data)}] 分析中: {job_id}")
        
        # 使用LLM分析
        analysis_result = analyze_job_with_llm(llm_client, job_data)
        
        # 检查是否符合条件
        llm_analysis = analysis_result.get("llm_analysis", {})
        is_qualified = llm_analysis.get("is_qualified", False)
        analysis_detail = llm_analysis.get("analysis", {})
        qualification_reason = analysis_detail.get("reasoning", "")
        
        # 记录到已分析表中
        analyzed_record = {
            "id": job_id,
            "url": job_url,
            "is_qualified": is_qualified,
            "createdAt": current_time,
            "reason": qualification_reason
        }
        new_analyzed_records.append(analyzed_record)
        
        if is_qualified:
            new_qualified_jobs.append(analysis_result)
            print("✅ 符合条件")
        else:
            print("❌ 不符合条件")
    
    print(f"\n📈 数据处理完成！跳过 {skipped_count} 个已分析项，新增 {len(new_qualified_jobs)} 个符合条件的招聘信息")
    
    return new_analyzed_records, new_qualified_jobs


def handle_results(new_analyzed_records: List[Dict[str, Any]], 
                  new_qualified_jobs: List[Dict[str, Any]]) -> None:
    """
    后续动作函数：负责存储、通知等操作
    
    Args:
        new_analyzed_records: 新的已分析记录列表
        new_qualified_jobs: 新的符合条件的职位列表
    """
    print("\n=== 开始后续动作阶段 ===\n")
    
    # 加载现有数据
    analyzed_json_path = ".data/analyzed_jobs.json"
    jobs_json_path = ".data/jobs.json"
    
    # 加载现有的已分析记录
    existing_analyzed_jobs = []
    if os.path.exists(analyzed_json_path):
        try:
            with open(analyzed_json_path, "r", encoding="utf-8") as f:
                existing_analyzed_jobs = json.load(f)
        except Exception as e:
            print(f"⚠️ 加载现有已分析记录失败: {e}")
            existing_analyzed_jobs = []
    
    # 加载现有的符合条件的结果
    existing_qualified_results = []
    if os.path.exists(jobs_json_path):
        try:
            with open(jobs_json_path, "r", encoding="utf-8") as f:
                existing_qualified_results = json.load(f)
        except Exception as e:
            print(f"⚠️ 加载现有符合条件结果失败: {e}")
            existing_qualified_results = []
    
    # 更新已分析记录表：新记录在前面
    all_analyzed_jobs = new_analyzed_records + existing_analyzed_jobs
    
    # 保存已分析记录表
    print(f"💾 保存已分析记录表...（总共 {len(all_analyzed_jobs)} 个已分析记录）")
    with open(analyzed_json_path, "w", encoding="utf-8") as f:
        json.dump(all_analyzed_jobs, f, ensure_ascii=False, indent=2)
    
    # 合并符合条件的数据：新数据在前面
    all_qualified_jobs = new_qualified_jobs + existing_qualified_results
    
    # 保存符合条件的JSON文件
    print(f"💾 保存符合条件的数据...（总共 {len(all_qualified_jobs)} 个符合条件的招聘信息）")
    with open(jobs_json_path, "w", encoding="utf-8") as f:
        json.dump(all_qualified_jobs, f, ensure_ascii=False, indent=2)
    
    # 生成Markdown
    print("📝 生成Markdown报告...")
    markdown_content = create_markdown_table(all_qualified_jobs)
    
    # 写入文件
    with open(".data/jobs.md", "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    print("✅ 报告已保存到 jobs.json 和 jobs.md")
    
    # 保存新的符合条件的职位到通知文件
    if new_qualified_jobs:
        save_notifications(new_qualified_jobs)


def main():
    """主函数：协调数据处理和后续动作"""
    print("=== 开始招聘信息分析流程 ===\n")
    
    try:
        # 第一阶段：数据处理
        new_analyzed_records, new_qualified_jobs = process_data()
        
        # 第二阶段：后续动作
        handle_results(new_analyzed_records, new_qualified_jobs)
        
        print(f"\n🎉 流程完成！新增 {len(new_qualified_jobs)} 个符合条件的招聘信息")
        
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()