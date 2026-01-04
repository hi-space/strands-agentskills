"""Streamlit Meta-Tool Demo - 세 가지 실행 모드 비교

이 Streamlit 앱은 세 가지 Agent Skills 실행 모드를 시각적으로 비교합니다:
1. File-based Mode: LLM이 file_read로 SKILL.md 직접 읽기
2. Tool-based Mode: skill tool로 instructions 로드
3. Meta-Tool Mode: Sub-agent를 tool로 사용 (Agent as Tool 패턴)
"""

import sys
from pathlib import Path
import logging
import os

os.environ["BYPASS_TOOL_CONSENT"] = "true"
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from strands import Agent
from strands.models import BedrockModel
from strands_tools import file_read, file_write, shell, editor
from agentskills import (
    discover_skills,
    generate_skills_prompt,
    create_skill_tool,
    create_skill_agent_tool,
    get_bedrock_agent_model,
)
from utils.strands_stream import StreamlitStreamRenderer

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)
logging.getLogger("opentelemetry.context").setLevel(logging.CRITICAL)

# 페이지 설정
st.set_page_config(
    page_title="Agent Skills - Multi-Agent Mode Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Helper functions removed - now handled by StreamlitStreamRenderer


def init_session_state():
    """Session state 초기화"""
    if "skills" not in st.session_state:
        st.session_state.skills = []
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "mode" not in st.session_state:
        st.session_state.mode = "Meta-Tool Mode"


def create_agent_by_mode(skills, skills_dir, mode: str):
    """선택된 모드에 따라 Agent 생성"""
    skills_prompt = generate_skills_prompt(skills)
    
    agent_model = get_bedrock_agent_model(thinking=True)
    default_tools = [file_read, file_write, shell, editor]

    if mode == "File-based Mode":
        agent = Agent(
            system_prompt=skills_prompt,
            tools=default_tools,
            model=agent_model,
            callback_handler=None,
        )
        return agent

    elif mode == "Tool-based Mode":
        skill_tool = create_skill_tool(skills, skills_dir)

        agent = Agent(
            system_prompt=skills_prompt,
            tools=[skill_tool, *default_tools],
            model=agent_model,
            callback_handler=None,
        )
        return agent

    else:  # Meta-Tool Mode
        # Sub-agent를 tool로 사용 - Strands의 "Agents as Tools" 패턴
        meta_tool = create_skill_agent_tool(
            skills,
            skills_dir,
            base_agent_model=agent_model,
            additional_tools=default_tools
        )

        agent = Agent(
            system_prompt=skills_prompt,
            tools=[meta_tool],
            model=agent_model,
            callback_handler=None,
        )
        
        return agent


async def streaming_generator(agent_stream):
    """스트리밍 이벤트를 처리하고 텍스트와 tool 호출 정보를 yield
    
    StreamlitStreamRenderer를 사용하여 이벤트를 처리합니다.
    Strands SDK의 tool_stream_event 패턴을 사용하여 Sub-agent 이벤트를 처리합니다.
    """
    renderer = StreamlitStreamRenderer()

    try:
        async for event in agent_stream:
            if isinstance(event, dict):
                # Process event through renderer
                results = renderer.process(event)
                for result in results:
                    if result:  # Only yield non-empty strings
                        yield result

        logger.info("✅ Agent 실행 완료")

    except Exception as e:
        logger.error(f"스트리밍 오류: {str(e)}")
        yield f"\n\n❌ 오류 발생: {str(e)}\n"
        raise


# 메인 UI
st.title("🤖 Strands AgentSkills")
st.subheader("🔍 Streamlit Integration Demo")
st.markdown("""> 세 가지 Agent Skills 실행 모드를 비교하고, 실제 에이전트의 SKILLS 호출 동작을 시각적으로 확인할 수 있습니다.""")

# Session state 초기화
init_session_state()

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")

    # 모드 선택
    mode_options = ["Meta-Tool Mode", "Tool-based Mode", "File-based Mode"]
    selected_mode = st.selectbox(
        "실행 모드 선택:",
        mode_options,
        index=0,
        key="mode_select"
    )

    # 모드 설명
    mode_descriptions = {
        "File-based Mode": "📄 LLM이 file_read로 SKILL.md 직접 읽기\n- 가장 자연스러운 방식\n- 일반적인 사용에 권장",
        "Tool-based Mode": "🔧 skill tool로 instructions 로드\n- 구조화된 접근\n- 명시적 skill 활성화",
        "Meta-Tool Mode": "🔗 Sub-agent를 tool로 사용\n- Agent as Tool 패턴\n- 완전한 context 분리"
    }

    st.info(mode_descriptions[selected_mode])

    st.divider()

    # Skills 로드
    skills_dir = Path(__file__).parent.parent.parent / "skills"
    st.caption(f"Skills 디렉토리: `{skills_dir.name}`")

    if st.button("🔄 Skills 다시 로드", use_container_width=True):
        with st.spinner("Skills 로드 중..."):
            st.session_state.skills = discover_skills(skills_dir)
            if st.session_state.skills:
                st.session_state.agent = create_agent_by_mode(
                    st.session_state.skills,
                    skills_dir,
                    selected_mode
                )
                st.session_state.mode = selected_mode
                st.success(f"✅ {len(st.session_state.skills)}개 Skills 로드!")
            else:
                st.warning("⚠️ Skills를 찾을 수 없습니다.")
        st.rerun()

    # 모드가 변경되었으면 agent 재생성
    if st.session_state.mode != selected_mode and st.session_state.skills:
        st.session_state.agent = create_agent_by_mode(
            st.session_state.skills,
            skills_dir,
            selected_mode
        )
        st.session_state.mode = selected_mode

    if st.session_state.skills:
        st.divider()
        st.subheader("📦 발견된 Skills")
        for skill in st.session_state.skills:
            with st.expander(f"**{skill.name}**"):
                st.caption(skill.description)
                st.caption(f"📁 `{Path(skill.path).parent.name}`")


# 메인 컨텐츠
if not st.session_state.skills:
    st.warning("⚠️ 사이드바에서 'Skills 다시 로드'를 클릭하여 Skills를 로드해주세요.")
    st.info("💡 Skills가 로드되면 질의를 입력하여 각 모드의 동작을 확인할 수 있습니다.")
else:
    # 현재 모드 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("현재 모드", st.session_state.mode)
    with col2:
        st.metric("발견된 Skills", len(st.session_state.skills))
    with col3:
        status = "✅ 준비 완료" if st.session_state.agent else "❌ 미준비"
        st.metric("Agent 상태", status)

    st.divider()

    # 질의 입력
    st.header("💬 Agent 질의 실행")

    query = st.text_input(
        "질의 입력:",
        "sales_data 파일을 분석하고, 시각화 이미지를 첨부하여 pptx 파일로 만들어주세요",
        placeholder="Agent에게 질의를 입력하세요",        
        key="query_input",
    )

    run_button = st.button("🚀 실행", use_container_width=True, type="primary")

    # Agent 실행
    if run_button and query:
        # 질의 표시
        with st.chat_message("user"):
            st.write(query)

        # Agent 응답
        with st.chat_message("assistant"):
            if hasattr(st.session_state.agent, "stream_async"):
                logger.info(f"🚀 Agent 실행 시작 [{st.session_state.mode}]: {query}")
                
                # Strands SDK의 tool_stream_event 패턴으로 Sub-agent 스트리밍 처리
                agent_stream = st.session_state.agent.stream_async(query)
                st.write_stream(streaming_generator(agent_stream))
            else:
                st.error("스트리밍이 지원되지 않는 Agent입니다.")

        st.success("✅ 실행 완료!")


# 하단 정보
st.divider()
st.caption("""
**💡 Tips:**
- Meta-Tool Mode: Agent as Tool 패턴 - 각 Skill이 독립된 Sub-agent(tool)에서 실행됩니다
- Tool-based Mode: skill tool 호출을 통한 명시적 activation을 볼 수 있습니다
- File-based Mode: LLM이 file_read tool을 사용하여 SKILL.md를 직접 읽는 자연스러운 방식입니다
""")
