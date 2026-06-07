from datetime import datetime
import re, json
import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ========== 页面配置 ==========
st.set_page_config(
    page_title="招聘Agent Demo - AI智能匹配",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": """
# ======== 招聘Agent v1.0 Demo ========
由 AI 驱动的智能招聘系统（演示版）
"""
    }
)

# ========== 抑制JS错误 ==========
st.markdown("""
<script>
const _origRemoveChild = Node.prototype.removeChild;
Node.prototype.removeChild = function(child) {
  try {
    return _origRemoveChild.call(this, child);
  } catch (e) {
    if (e.name === 'NotFoundError' && e.message.includes('removeChild')) {
      return child;
    }
    throw e;
  }
};
</script>
""", unsafe_allow_html=True)

# ========== 侧边栏 ==========
st.sidebar.title("🚀 招聘Agent Demo")
st.sidebar.markdown("---")

# API Key 输入
st.sidebar.subheader("🔑 API 配置")
api_key = st.sidebar.text_input(
    "OpenAI API Key",
    type="password",
    help="请输入你的 OpenAI API Key"
)

if api_key:
    os.environ["OPENAI_API_KEY"] = api_key
    st.sidebar.success("✅ API Key 已设置")
else:
    st.sidebar.warning("⚠️ 请输入 API Key")

st.sidebar.markdown("---")

# 演示说明
st.sidebar.subheader("📖 使用说明")
st.sidebar.markdown("""
1. 输入 OpenAI API Key
2. 上传简历文件（PDF/DOCX）
3. 输入职位描述
4. 点击「开始匹配」查看结果
""")

st.sidebar.markdown("---")
st.sidebar.caption("⚠️ 演示版：数据不会保存")

# ========== 主界面 ==========
st.title("🚀 招聘Agent - AI智能匹配（演示版）")
st.markdown("### 上传简历 + 职位描述 → AI自动匹配分析")

# 检查 API Key
if not api_key:
    st.warning("⚠️ 请在左侧边栏输入 OpenAI API Key")
    st.stop()

# ========== 文件上传区域 ==========
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 上传简历")
    uploaded_file = st.file_uploader(
        "选择简历文件",
        type=["pdf", "docx", "txt"],
        help="支持 PDF、DOCX、TXT 格式"
    )
    
    if uploaded_file:
        st.success(f"✅ 已上传：{uploaded_file.name}")

with col2:
    st.subheader("💼 职位描述")
    job_title = st.text_input("职位名称", placeholder="例如：Python后端工程师")
    job_desc = st.text_area(
        "职位描述",
        height=200,
        placeholder="请输入职位描述、要求和职责..."
    )
    
    job_requirements = st.text_area(
        "任职要求（可选）",
        height=100,
        placeholder="请输入具体任职要求..."
    )

# ========== 开始匹配 ==========
st.markdown("---")

if st.button("🚀 开始匹配", use_container_width=True, type="primary"):
    if not uploaded_file:
        st.error("❌ 请先上传简历文件")
        st.stop()
    
    if not job_desc:
        st.error("❌ 请先输入职位描述")
        st.stop()
    
    # 显示进度
    with st.spinner("🔍 正在解析简历..."):
        try:
            # 保存上传的文件到临时目录
            temp_path = os.path.join(os.getcwd(), "temp_resume_" + uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 解析简历
            from resume_parser import parse_resume_file, parse_resume_with_ai
            
            # 基础解析
            resume_text = parse_resume_file(temp_path)
            parsed_data = parse_resume_with_ai(resume_text, api_key)
            
            st.success("✅ 简历解析完成！")
            
        except Exception as e:
            st.error(f"❌ 简历解析失败：{e}")
            st.stop()
    
    with st.spinner("🤖 AI匹配分析中..."):
        try:
            # AI匹配
            from ai_match import ai_match_resume
            
            job_dict = {
                "title": job_title,
                "description": job_desc,
                "requirements": job_requirements
            }
            
            match_result = ai_match_resume(
                job=job_dict,
                resume_parsed=parsed_data,
                api_key=api_key,
                api_base="https://api.openai.com/v1",
                model="gpt-4"
            )
            
            st.success("✅ 匹配分析完成！")
            
        except Exception as e:
            st.error(f"❌ AI匹配失败：{e}")
            st.stop()
    
    # ========== 显示匹配结果 ==========
    st.markdown("---")
    st.header("📊 匹配结果")
    
    # 评分
    score = match_result.get("match_score", 0)
    st.metric("匹配评分", f"{score}/100")
    
    # 进度条
    st.progress(score / 100)
    
    if score >= 80:
        st.success("🌟 高度匹配！建议优先安排面试")
    elif score >= 60:
        st.warning("✅ 中等匹配，可以考虑面试")
    else:
        st.error("⚠️ 匹配度较低，建议谨慎考虑")
    
    # 详细信息
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ 候选人优势")
        highlights = match_result.get("highlights", [])
        if highlights:
            for item in highlights:
                st.markdown(f"- {item}")
        else:
            st.info("未提取到明显优势")
    
    with col2:
        st.subheader("⚠️ 潜在顾虑")
        concerns = match_result.get("concerns", [])
        if concerns:
            for item in concerns:
                st.markdown(f"- {item}")
        else:
            st.info("无明显顾虑")
    
    # 推荐建议
    st.subheader("💡 AI推荐建议")
    recommendation = match_result.get("recommendation", "")
    if recommendation:
        st.info(recommendation)
    
    # 维度分析
    st.subheader("📈 各维度评分")
    dimensions = match_result.get("dimensions", {})
    if dimensions:
        for dim, score_val in dimensions.items():
            st.text(f"{dim}: {score_val}/100")
            st.progress(score_val / 100)
    
    # 清理临时文件
    try:
        os.remove(temp_path)
    except:
        pass

# ========== 页脚 ==========
st.markdown("---")
st.caption("招聘Agent Demo v1.0 | 由 AI 驱动 | 演示版数据不保存")
