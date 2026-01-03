# Agent Skills 예제

Strands Agents SDK와 Progressive Disclosure를 사용하는 완전한 예제들입니다.

## 사전 준비

```bash
# 의존성 설치
pip install strands-agents strands-agents-tools pyyaml

# agentskills 설치
cd strands_agentskills
pip install -e .
```

## 예제 목록

### 1. [1-discovery_skills.py](1-discovery_skills.py) ⭐ 여기서 시작

Filesystem-Based 접근 방식의 기본 예제입니다. 3단계 Progressive Disclosure를 완전히 보여줍니다.

```bash
python examples/1-discovery_skills.py
```

**시연 내용:**
- **Phase 1**: Skill discovery (metadata만 system prompt에 로드)
- **Phase 2**: LLM이 file_read로 SKILL.md 읽기 (true progressive disclosure)
- **Phase 3**: LLM이 필요시 resources 읽기
- TerminalStreamRenderer로 컬러풀한 스트리밍 출력

**추천 대상:** 빠른 통합 가이드가 필요한 경우, 가장 자연스러운 사용 방식

---

### 2. [2-skill_tool_with_progressive_disclosure.py](2-skill_tool_with_progressive_disclosure.py) 🔧 Tool-Based

Tool-Based 접근 방식의 예제입니다. skill tool을 통해 명시적으로 instructions를 로드합니다.

```bash
python examples/2-skill_tool_with_progressive_disclosure.py
```

**시연 내용:**
- **Phase 1**: Discovery - metadata 로드 (~100 tokens/skill)
- **Phase 1.5**: System prompt 생성 및 skill tool 연결
- **Phase 2**: skill(skill_name=...) 호출로 instructions 로드
- 각 단계별 토큰 사용량 추정
- 구조화된 접근 방식

**추천 대상:** 명시적 skill activation이 필요한 경우

---

### 3. [3-skill_agent_tool.py](3-skill_agent_tool.py) 🔗 Meta-Tool Mode (Agent as Tool)

Meta-Tool 접근 방식의 예제입니다. 각 Skill이 독립된 Sub-agent를 tool로 사용하여 격리 실행됩니다.

```bash
python examples/3-skill_agent_tool.py
```

**시연 내용:**
- Skill agent tool 생성 (use_skill) - Agent as Tool 패턴
- 각 skill이 isolated sub-agent (as a tool)에서 실행
- Sub-agent가 자체 context와 SKILL.md를 system prompt로 사용
- 완전한 context 분리 (main agent와 격리)
- Sub-agent에 file_read, file_write, shell 도구 제공

**추천 대상:** Context 격리가 필요한 경우, 모듈화된 실행이 필요한 경우

---

### 4. [4-streamlit_prompt_simulation.py](4-streamlit_prompt_simulation.py) 🎨 시각화 데모

Streamlit 기반의 Progressive Disclosure 시각화 데모입니다. Phase 1→2→3을 탭으로 구분하여 각 단계에서 무엇이 로드되고 Agent의 prompt에 어떻게 포함되는지 확인할 수 있습니다.

```bash
# Streamlit 설치 필요
pip install streamlit

# 실행
streamlit run examples/4-streamlit_prompt_simulation.py
```

**시연 내용:**
- **Phase 1 탭**: Discovery - Skills 발견 및 metadata 표시, 생성된 System Prompt 확인
- **Phase 2 탭**: Activation - Skill 활성화 시뮬레이션, Instructions 로드 및 Tool 호출 추적
- **Phase 3 탭**: Resources - Resource 파일 목록 및 읽기 시뮬레이션, 토큰 사용량 시각화
- 각 Phase별 토큰 사용량 추정 및 비교
- Tool 호출 추적 및 Prompt 내용 실시간 확인

**추천 대상:** Progressive Disclosure의 작동 방식을 시각적으로 이해하고 싶은 경우

---

### 5. [5-streamlit_strands_integration.py](5-streamlit_strands_integration.py) 🚀 세 가지 모드 비교 데모

세 가지 Agent Skills 실행 모드(File-based, Tool-based, Multi-Agent)를 비교하고 실시간으로 동작을 확인할 수 있는 Streamlit 앱입니다.

```bash
# Streamlit 설치 필요
pip install streamlit

# 실행
streamlit run examples/5-streamlit_strands_integration.py
```

**시연 내용:**
- **File-based Mode**: LLM이 file_read로 SKILL.md 직접 읽기 (가장 자연스러운 방식)
- **Tool-based Mode**: skill tool 호출을 통한 명시적 activation
- **Meta-Tool Mode**: Sub-agent를 tool로 사용하여 격리 실행 (Agent as Tool 패턴)
- 실시간 스트리밍 응답 및 Tool 호출 시각화
- 모드 간 전환 및 비교
- StreamlitStreamRenderer로 Sub-agent 이벤트 처리

**추천 대상:** 세 가지 모드의 차이점을 비교하고 싶은 경우, 실제 Agent 동작 확인

---

## 세 가지 실행 모드 비교

| 모드 | 파일 | 특징 | 추천 대상 |
|------|------|------|----------|
| **File-based** | 1-discovery_skills.py | LLM이 file_read로 직접 읽기 | 가장 자연스러운 방식 |
| **Tool-based** | 2-skill_tool_with_progressive_disclosure.py | skill tool로 명시적 로드 | 구조화된 접근 필요시 |
| **Meta-Tool** | 3-skill_agent_tool.py | Sub-agent를 tool로 사용 | Context 분리 필요시 |

---

## Progressive Disclosure 실제 동작

### Phase 1: Discovery (시작 시)
```python
from agentskills import discover_skills

# 로드: name, description, path, allowed_tools
# 토큰 비용: ~100 tokens per skill
skills = discover_skills("./skills")

for skill in skills:
    print(f"{skill.name}: {skill.description}")
```

### Phase 2: Activation (필요 시)
```python
from agentskills import load_instructions

# Tool을 통해 자동
response = await agent.invoke_async("web-research 스킬 사용해줘")

# 수동
instructions = load_instructions(skill.path)
# 토큰 비용: <5000 tokens per skill
```

### Phase 3: Resources (참조 시)
```python
from agentskills import load_resource

# instructions에서 참조된 특정 파일 로드
api_docs = load_resource(skill.skill_dir, "references/api-docs.md")
helper = load_resource(skill.skill_dir, "scripts/helper.py")
```

---

## 예제 실행

`skills/` 디렉토리에 Skill이 있는지 확인하세요:

```
skills/
├── web-research/
│   ├── SKILL.md
│   ├── scripts/
│   │   └── search.py
│   └── references/
│       └── apis.md
└── file-processing/
    └── SKILL.md
```

스킬 형식 표준은 [AgentSkills.io](https://agentskills.io)를 참고하세요.

---

## 예제 출력

### 1-discovery_skills.py (File-based)

```
🚀 Agent Skills - Progressive Disclosure Demo

============================================================
Phase 1: Discovery (Metadata Only)
============================================================

✓ Discovered 2 skills:

  📦 web-research
     Description: 웹 검색과 분석을 통해 포괄적인 리서치 수행
     Location: /path/to/skills/web-research/SKILL.md
     Allowed tools: WebFetch, Grep

============================================================
Example 2: LLM reads SKILL.md on demand (Phase 2)
============================================================

Asking: 'How do I use the web-research skill?'
✓ Agent read the SKILL.md only when needed (true progressive disclosure)
```

### 3-skill_agent_tool.py (Meta-Tool / Agent as Tool)

```
🚀 Agent Skills - Meta-Tool Mode Demo (Agent as Tool)

============================================================
Creating Skill Agent Tool (Agent as Tool)
============================================================

🔧 Skill agent tool created: use_skill
   ✓ Each skill runs in isolated sub-agent (as a tool)
   ✓ Sub-agent has: file_read, file_write, shell
   ✓ Complete context separation from main agent

============================================================
Example: Execute skill in isolated sub-agent (as a tool)
============================================================

✓ Skill executed in isolated sub-agent (as a tool)
✓ Sub-agent had its own context with SKILL.md as system prompt
✓ Main agent received result without seeing internal execution
```

---

## 토큰 효율성

Progressive Disclosure는 컨텍스트 사용을 최소화합니다:

| Phase | 시점 | 내용 | 토큰 |
|-------|------|------|--------|
| 1 | 시작 시 | 모든 스킬 metadata | ~100/skill |
| 2 | 활성화 | 단일 스킬 instructions | <5000 |
| 3 | 필요 시 | 개별 resource 파일 | 가변 |

**10개 스킬 예시:**
- Phase 1: ~1,000 tokens (모든 스킬)
- Phase 2: ~3,000 tokens (1개 활성화된 스킬)
- Phase 3: ~500 tokens (2개 resource 파일)
- **총합: ~4,500 tokens** (vs Progressive Disclosure 없이 ~50,000 tokens!)

---

## 고급 사용법

### Meta-Tool Mode 커스텀 설정 (Agent as Tool)

```python
from agentskills import create_skill_agent_tool

# Sub-agent에 추가 도구 제공
skill_agent_tool = create_skill_agent_tool(
    skills,
    skills_dir,
    additional_tools=[file_read, file_write, shell]
)

agent = Agent(
    tools=[skill_agent_tool],  # use_skill만 제공
    ...
)
```

### 스킬 resource 접근

```python
from agentskills import load_resource

# Agent가 실행 중에 resource 요청 가능
api_docs = load_resource(skill.skill_dir, "references/api-docs.md")
helper = load_resource(skill.skill_dir, "scripts/helper.py")
```

---

## 문제 해결

**Skill을 찾을 수 없음:**
- `skills/` 디렉토리가 존재하는지 확인
- 각 Skill에 YAML frontmatter가 있는 `SKILL.md` 파일이 있는지 확인

**Import 에러:**
- 패키지 설치: `pip install -e strands_agentskills/`
- Python 경로 확인

**Model 에러:**
- Bedrock용 AWS 자격증명 확인
- 또는 다른 모델 사용: `model="global.anthropic.claude-haiku-4-5-20251001-v1:0"`

---

## 더 알아보기

- [AgentSkills.io 표준 문서](https://agentskills.io/specification)
- [Strands Agents SDK 문서](https://strandsagents.com)
- [메인 README](../../README.md)
