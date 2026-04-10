"""
单个招聘信息测试脚本

用于测试单个招聘详情页面的抓取和分析，
将结果打印到终端而不保存文件，适合调试和快速验证。
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any

from core.fetch import fetch_page
from sources.parsers.eleduck_detail import analyze_eleduck_page, extract_text_content
from llm.openai import OpenAIChat
from core.analyzer import analyze_job_with_llm

# 加载环境变量
load_dotenv()

source_detail: str = (
    "https://eleduck.com/tposts/gYfZOZ"  # 可以修改这个URL来测试不同的招聘信息
)

# 移除不需要的列表和分页参数

# 配置日志
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def process_data() -> Dict[str, Any]:
    """
    数据处理函数：负责抓取单个详情页面并分析招聘信息

    Returns:
        Dict[str, Any]: 分析结果
    """
    print("=== 开始数据处理阶段 ===\n")

    # 初始化LLM客户端
    print("🚀 初始化LLM客户端...")
    llm_client = OpenAIChat()

    # 抓取单个详情页面
    print(f"\n📥 开始抓取详情页面: {source_detail}")
    html_content = fetch_page(source_detail)

    if not html_content:
        print("❌ 没有获取到页面内容")
        return None

    # 确保.data目录存在
    os.makedirs(".data", exist_ok=True)

    # 保存HTML到临时文件
    temp_html_path = ".data/temp_detail.html"
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 解析页面内容
    print("\n📊 解析页面内容...")
    parsed_result = analyze_eleduck_page(temp_html_path)

    # 构造job_data格式以兼容现有的分析函数
    job_data = {
        "title": parsed_result.get("title", ""),
        "content": extract_text_content(parsed_result),
        "tags": parsed_result.get("tags", []),
        "list_metadata": {
            "url": source_detail,
            "id": source_detail.split("/")[-1],  # 从URL提取ID
            "title": parsed_result.get("title", ""),
        },
    }

    print(f"\n🔍 开始LLM分析...")

    # 使用LLM分析
    analysis_result = analyze_job_with_llm(llm_client, job_data)

    # 检查是否符合条件
    llm_analysis = analysis_result.get("llm_analysis", {})
    is_qualified = llm_analysis.get("is_qualified", False)

    if is_qualified:
        print("✅ 符合条件")
    else:
        print("❌ 不符合条件")

    # 清理临时文件
    if os.path.exists(temp_html_path):
        os.remove(temp_html_path)

    print(f"\n📈 数据处理完成！")

    return analysis_result


def handle_results(analysis_result: Dict[str, Any]) -> None:
    """
    后续动作函数：只打印结果，不保存

    Args:
        analysis_result: 分析结果
    """
    print("\n=== 分析结果 ===\n")

    if not analysis_result:
        print("❌ 没有分析结果")
        return

    # 获取分析数据
    llm_analysis = analysis_result.get("llm_analysis", {})
    original_data = analysis_result.get("original_data", {})
    list_metadata = original_data.get("list_metadata", {})

    # 打印基本信息
    print(f"📄 文章URL: {list_metadata.get('url', '未知')}")
    print(f"📝 文章标题: {list_metadata.get('title', '未知')}")
    print(f"🆔 文章ID: {list_metadata.get('id', '未知')}")

    # 打印分析结果
    is_qualified = llm_analysis.get("is_qualified", False)
    print(f"\n✅ 是否符合条件: {'是' if is_qualified else '否'}")

    # 打印提取的信息
    extracted_info = llm_analysis.get("extracted_info", {})
    if extracted_info:
        print("\n📊 提取的信息:")
        for key, value in extracted_info.items():
            print(f"  {key}: {value}")

    # 打印分析详情
    analysis_detail = llm_analysis.get("analysis", {})
    if analysis_detail:
        print("\n🔍 分析详情:")
        reasoning = analysis_detail.get("reasoning", "")
        if reasoning:
            print(f"  推理过程: {reasoning}")

    print("\n=== 分析完成 ===\n")


def main():
    """主函数：协调数据处理和结果展示"""
    print("=== 开始单个招聘信息分析流程 ===\n")

    try:
        # 第一阶段：数据处理
        analysis_result = process_data()

        # 第二阶段：结果展示
        handle_results(analysis_result)

        print(f"\n🎉 流程完成！")

    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
