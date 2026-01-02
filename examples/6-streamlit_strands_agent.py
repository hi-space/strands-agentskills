"""Streamlit Live Demo - 실제 Strands Agents SDK 실행 시각화

이 Streamlit 앱은 실제 Strands Agents SDK를 사용하여 질의를 받고
자동으로 Phase 1->2->3을 순차적으로 수행하는 과정을 실시간으로 시각화합니다.
Agent가 어떻게 Progressive Disclosure를 수행하는지 확인할 수 있습니다.
"""

import sys
from pathlib import Path
from typing import Any
import time
import logging
import os

os.environ["BYPASS_TOOL_CONSENT"] = "true"
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from strands import Agent
from strands_tools import file_read, file_write, shell
from agentskills import (
    discover_skills,
    generate_skills_prompt,
    create_skill_tool,
)


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 콘솔 출력
    ]
)
logger = logging.getLogger(__name__)

# OpenTelemetry context 에러 무시 (asyncio event loop와의 충돌로 인한 경고성 에러)
logging.getLogger("opentelemetry.context").setLevel(logging.CRITICAL)

# 페이지 설정
st.set_page_config(
    page_title="Agent Skills - Live Execution Demo",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)


def estimate_tokens(text: str) -> int:
    """대략적인 토큰 수 추정 (1 token ≈ 4 characters)"""
    return len(text) // 4


def format_number(num: int) -> str:
    """숫자를 읽기 쉬운 형식으로 변환"""
    if num >= 1000:
        return f"{num / 1000:.1f}K"
    return str(num)


def extract_tool_result_content(tool_result: Any) -> str:
    """Tool 결과에서 텍스트 content를 추출"""
    if not isinstance(tool_result, dict):
        return str(tool_result)
    
    # content 필드 확인
    if "content" in tool_result:
        content = tool_result["content"]
        if isinstance(content, list) and len(content) > 0:
            # 리스트의 첫 번째 항목 확인
            first_item = content[0]
            if isinstance(first_item, dict) and "text" in first_item:
                return first_item["text"]
            return str(first_item)
        elif isinstance(content, str):
            return content
        return str(content)
    
    # text 필드 확인
    if "text" in tool_result:
        return tool_result["text"]
    
    # 그 외의 경우 전체를 문자열로 변환
    return str(tool_result)


def format_tool_display(tool_name: str, args: dict) -> str:
    """Tool 이름과 arguments를 표시 형식으로 포맷팅"""
    if not args:
        return f"{tool_name}()"
    return f"{tool_name}({', '.join(f'{k}={v!r}' for k, v in args.items())})"


def extract_tool_use_from_event(event: dict) -> dict | None:
    """이벤트에서 toolUse 정보 추출"""
    tool_use = None
    
    # 최상위 레벨에서 toolUse 확인
    if "toolUse" in event:
        tool_use = event["toolUse"]
    # message -> content -> toolUse 구조 확인
    elif "message" in event:
        message = event["message"]
        if isinstance(message, dict):
            content_list = message.get("content", [])
            if isinstance(content_list, list):
                for content in content_list:
                    if isinstance(content, dict) and "toolUse" in content:
                        tool_use = content["toolUse"]
                        break
    
    return tool_use if isinstance(tool_use, dict) else None


# Session state 초기화
def init_session_state():
    """Session state 초기화"""
    if "skills" not in st.session_state:
        st.session_state.skills = []
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "tracker" not in st.session_state:
        st.session_state.tracker = {
            "prompt_content": {
                "initial_system_prompt": "",
                "tool_results": [],
            },
            "is_running": False,
            "execution_history": [],
        }


def create_agent(skills, skills_dir):
    """Strands Agent 생성 (Hook을 사용한 tool 호출 추적)"""
    base_prompt = "You are a helpful AI assistant with access to specialized skills."
    skills_prompt = generate_skills_prompt(skills)
    full_prompt = f"{base_prompt}\n\n{skills_prompt}"
    
    # 원본 tool 생성 (추적 래퍼 없이)
    skill_tool = create_skill_tool(skills, skills_dir)
    
    # Agent 생성 (스트리밍을 위해 callback_handler=None)
    # Tool 호출은 스트리밍 이벤트에서 추적
    agent = Agent(
        system_prompt=full_prompt,
        tools=[skill_tool, file_read, file_write],  # 원본 tool 사용
        model="global.anthropic.claude-haiku-4-5-20251001-v1:0",
        callback_handler=None,  # 스트리밍을 위해 callback handler 비활성화
    )
    
    # System prompt 추적
    st.session_state.tracker["prompt_content"]["initial_system_prompt"] = full_prompt
    
    return agent




def _extract_response_text(response) -> str:
    """Agent 응답에서 텍스트 추출 헬퍼 함수"""
    if hasattr(response, "content"):
        content = response.content
        if isinstance(content, list):
            return "\n".join(
                block.text if hasattr(block, "text") else str(block)
                for block in content
            )
        else:
            return str(content)
    else:
        return str(response)




async def streaming_generator(agent_stream, query: str):
    """스트리밍 이벤트를 처리하고 텍스트와 tool 호출 정보를 yield하는 async generator"""
    response_text = ""
    displayed_tool_calls = set()  # 이미 표시한 tool 호출 추적 (toolUseId 사용)
    
    try:
        async for event in agent_stream:
            # 이벤트가 딕셔너리인 경우 (스트리밍 이벤트)
            if isinstance(event, dict):
                # Tool 호출 시작 표시
                tool_use = extract_tool_use_from_event(event)
                
                if tool_use:
                    tool_use_id = tool_use.get("toolUseId", "")
                    tool_name = tool_use.get("name", "")
                    tool_input = tool_use.get("input", {}) if isinstance(tool_use.get("input"), dict) else {}
                    
                    # Tool 호출 시작 표시 (중복 방지)
                    if tool_use_id and tool_use_id not in displayed_tool_calls:
                        displayed_tool_calls.add(tool_use_id)
                        tool_display = format_tool_display(tool_name, tool_input)
                        
                        yield f"\n\n**🔧 Tool 호출:**\n"
                        yield f"```markdown\n{tool_display}\n```\n\n"
                        
                
                # 텍스트 델타 추출 (data 필드에 텍스트 델타가 있음)
                if "data" in event:
                    chunk_text = event["data"]
                    if chunk_text:  # 빈 문자열이 아닌 경우만 추가
                        response_text += chunk_text
                        yield chunk_text
                
                # 메시지 이벤트에서 toolResult 확인 및 표시
                if "message" in event:
                    message = event["message"]
                    if isinstance(message, dict):
                        content_list = message.get("content", [])
                        
                        if isinstance(content_list, list):
                            for content in content_list:
                                if isinstance(content, dict) and "toolResult" in content:
                                    tool_result = content.get("toolResult", {})
                                    tool_use = tool_result.get("toolUse", {}) if isinstance(tool_result, dict) else {}
                                    tool_name = tool_use.get("name", "") if isinstance(tool_use, dict) else ""
                                    tool_input = tool_use.get("input", {}) if isinstance(tool_use, dict) else {}
                                    
                                    # Tool 결과 추출
                                    result_content = extract_tool_result_content(tool_result)
                                    
                                    # Tool 결과 표시
                                    if result_content:
                                        tool_display = format_tool_display(tool_name, tool_input)
                                        token_count = estimate_tokens(result_content)
                                        
                                        yield f"\n\n**✅ Tool 결과: {len(result_content):,} chars"
                                        if token_count > 0:
                                            yield f" (~{format_number(token_count)} tokens)"
                                        yield "**\n\n"
                                        preview = result_content[:1000] + "\n...(생략)" if len(result_content) > 1000 else result_content
                                        yield f"```markdown\n{preview}\n```\n\n"
                                        yield "---\n\n"
            
            # 이벤트가 객체인 경우 (최종 응답 객체)
            elif hasattr(event, "content"):
                # 최종 응답이 완료된 경우
                final_text = _extract_response_text(event)
                if final_text and final_text != response_text:
                    # 이미 출력된 부분을 제외하고 나머지만 yield
                    remaining = final_text[len(response_text):]
                    if remaining:
                        yield remaining
                        response_text = final_text
        
        # 실행 완료
        st.session_state.tracker["is_running"] = False
        logger.info(f"✅ Agent 실행 완료: {len(response_text)} chars 응답 생성")
        
        
    except Exception as e:
        st.session_state.tracker["is_running"] = False
        logger.error(f"스트리밍 오류: {str(e)}")
        yield f"\n\n❌ 오류 발생: {str(e)}\n"
        raise




# 메인 타이틀
st.title("🚀 Agent Skills - Live Execution Demo")
st.markdown("""
이 데모는 **실제 Strands Agents SDK**를 사용하여 질의를 받고 자동으로 **Phase 1→2→3**을 
순차적으로 수행하는 과정을 실시간으로 시각화합니다. Agent가 Progressive Disclosure를 
어떻게 수행하는지 확인할 수 있습니다.
""")

# Session state 초기화
init_session_state()

# 사이드바
with st.sidebar:
    st.header("📋 설정")
    
    skills_dir = Path(__file__).parent.parent / "skills"
    st.info(f"Skills 디렉토리: `{skills_dir}`")
    
    if st.button("🔄 Skills 다시 로드", use_container_width=True, key="reload_skills"):
        with st.spinner("Skills 디렉토리를 스캔하는 중..."):
            st.session_state.skills = discover_skills(skills_dir)
            if st.session_state.skills:
                st.session_state.agent = create_agent(st.session_state.skills, skills_dir)
                st.success(f"✅ {len(st.session_state.skills)}개 Skills 로드 완료!")
            else:
                st.warning("⚠️ Skills를 찾을 수 없습니다.")
        st.rerun()
    
    if st.session_state.skills:
        st.divider()
        st.subheader("📦 발견된 Skills")
        for skill in st.session_state.skills:
            st.write(f"- **{skill.name}**: {skill.description}")


# 메인 컨텐츠
if not st.session_state.skills:
    st.warning("⚠️ 먼저 사이드바에서 'Skills 다시 로드' 버튼을 클릭하여 Skills를 로드해주세요.")
    st.info("💡 Skills가 로드되면 질의를 입력하여 Agent의 Progressive Disclosure 동작을 확인할 수 있습니다.")
else:
    # Phase 1 정보 표시
    st.header("📦 Phase 1: Discovery (완료)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("발견된 Skills", len(st.session_state.skills))
    with col2:
        initial_tokens = estimate_tokens(
            st.session_state.tracker["prompt_content"]["initial_system_prompt"]
        )
        st.metric("System Prompt 토큰", f"~{format_number(initial_tokens)}")
    with col3:
        st.metric("Agent 상태", "✅ 준비 완료" if st.session_state.agent else "❌ 미준비")
    
    st.divider()
    
    # 질의 입력 및 실행
    st.header("💬 Agent 질의 실행")
    
    # 예제 질의
    example_queries = [
        "어떤 skills를 사용할 수 있나요??",
        "양자 컴퓨팅의 최근 근황에 대해 설명해주세요.",
        "skill-creator 사용법에 대해 설명해주세요."
    ]
    
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "질의 입력:",
            placeholder="에이전트에게 질의를 입력해주세요",
            key="query_input",
        )
    with col2:
        st.write("")  # 공간 맞추기
        st.write("")  # 공간 맞추기
        run_button = st.button("🚀 실행", use_container_width=True, type="primary")
    
    # 예제 질의 버튼
    st.write("**예제 질의:**")
    example_cols = st.columns(len(example_queries))
    for i, example in enumerate(example_queries):
        with example_cols[i]:
            if st.button(f"📝 {example[:30]}...", key=f"example_{i}", use_container_width=True):
                query = example
                run_button = True
    
    # 실시간 표시를 위한 컨테이너 생성
    prompt_container = st.empty()
    
    # Agent 실행
    if run_button and query:
        # 실행 전 초기화
        st.session_state.tracker["prompt_content"]["tool_results"] = []
        st.session_state.tracker["execution_history"] = []
        
        # 질의 표시
        with st.chat_message("user"):
            st.write(query)
        
        # 실행 히스토리에 질의 추가
        st.session_state.tracker["execution_history"].append({
            "type": "query",
            "content": query,
            "timestamp": time.time(),
        })
        
        # Agent 응답 스트리밍 표시
        with st.chat_message("assistant"):
            if hasattr(st.session_state.agent, "stream_async"):
                st.session_state.tracker["is_running"] = True
                logger.info(f"🚀 Agent 실행 시작: {query}")
                
                # 스트리밍을 위한 async generator 생성
                agent_stream = st.session_state.agent.stream_async(query)
                
                # st.write_stream은 async generator를 직접 지원
                st.write_stream(streaming_generator(agent_stream, query))
            else:
                # Streaming이 지원되지 않으면 일반 호출
                st.error("스트리밍이 지원되지 않는 Agent입니다.")
        
        st.success("✅ 실행 완료!")
    
    # 실행 상태 표시
    if st.session_state.tracker.get("is_running"):
        st.info("🔄 Agent가 실행 중입니다...")
    