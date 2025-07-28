import logging
import os
import tempfile
from tools.fetch_page import fetch_page
from tools.parse_detail_page import analyze_eleduck_page, extract_text_content

# 获取当前模块的logger
logger = logging.getLogger(__name__)


def fetch_and_parse_detail(url):
    """演示使用分离的 fetch 和 parse 功能爬取电鸭社区文章"""
    logger.debug("=== 电鸭社区文章爬取 Playground ===")
    
    # 目标URL
    
    logger.debug("步骤1: 使用 fetch_page 获取页面内容...")
    # 使用分离的 fetch 功能获取页面内容
    html_content = fetch_page(url)
    
    if not html_content:
        logger.debug("❌ 获取页面内容失败")
        return None
    
    logger.debug(f"✅ 成功获取页面内容，长度: {len(html_content)} 字符")
    
    logger.debug("\n步骤2: 创建临时HTML文件用于解析...")
    # 创建临时文件进行解析（因为 analyze_eleduck_page 需要文件路径）
    temp_file = None
    try:
        # 使用临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_file = f.name
        
        logger.debug(f"✅ 临时文件创建成功: {temp_file}")
        
        logger.debug("\n步骤3: 使用 parse_detail_page 解析页面内容...")
        result = analyze_eleduck_page(temp_file)
        
        logger.debug("步骤4: 输出解析结果...")
        formatted_content = extract_text_content(result)
        # logger.debug(f"\n📊 解析统计:")
        # logger.debug(f"   📰 页面标题: {result['title']}")
        # logger.debug(f"   📝 正文长度: {len(result['content'])} 字符")
        # logger.debug(f"   🏷️  标签数量: {len(result['tags'])}")
        # logger.debug(f"   📈 元数据: {result['meta_info']}")
        
        # logger.debug("\n" + "="*60)
        # logger.debug("📄 文章内容预览")
        # logger.debug("="*60)
        # logger.debug(formatted_content)
        # logger.debug(f"\n✅ 爬取完成！")
        return result
        
    except Exception as e:
        logger.debug(f"❌ 解析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # 清理临时文件
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
            logger.debug(f"🧹 已清理临时文件: {temp_file}")
