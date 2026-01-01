# Agent Skills 예제

Strands Agents SDK와 Progressive Disclosure를 사용하는 완전한 예제들입니다.

## 사전 준비

```bash
# 의존성 설치
pip install strands strictyaml

# agentskills 설치
cd strands_agentskills
pip install -e .
```

## 예제 목록

### 1. [basic_usage.py](basic_usage.py) ⭐ 여기서 시작

Strands SDK와 Agent Skills의 가장 간단한 사용법입니다.

```bash
python examples/basic_usage.py
```

**시연 내용:**
- Phase 1: Skill discovery (metadata만)
- Skill tool 생성
- 시스템 프롬프트 생성
- Strands Agent 생성 및 사용

**추천 대상:** 빠른 통합 가이드가 필요한 경우

---

### 2. [progressive_disclosure_demo.py](progressive_disclosure_demo.py)

3단계 Progressive Disclosure를 토큰 추적과 함께 시각적으로 보여줍니다.

```bash
python examples/progressive_disclosure_demo.py
```

**시연 내용:**
- **Phase 1**: Discovery - metadata 로드 (~100 tokens/skill)
- **Phase 2**: Activation - Instructions 로드 (<5000 tokens)
- **Phase 3**: Resources - 필요시 파일 로드
- 각 단계별 토큰 사용량 추정
- 완전한 흐름 시각화

**추천 대상:** Progressive Disclosure의 작동 방식 이해

---

### 3. [api_usage_demo.py](api_usage_demo.py) 📚 API 레퍼런스

각 단계별 정확한 API 호출을 코드 예제와 함께 보여줍니다.

```bash
python examples/api_usage_demo.py
```

**시연 내용:**
- 정확한 함수 시그니처와 사용법
- `discover_skills()`, `read_metadata()` (Phase 1)
- `read_instructions()` (Phase 2)
- `read_resource()` (Phase 3)
- Helper 함수: `generate_skills_prompt()`, `create_skill_tool()`

**추천 대상:** API 레퍼런스 및 구현 세부사항

---

### 4. [strands_integration.py](strands_integration.py) 🤖 완전한 통합

Strands Agent와 Progressive Disclosure의 완전한 통합 예제입니다.

```bash
python examples/strands_integration.py
```

**시연 내용:**
- 완전한 Strands Agent 통합
- Skill activation를 포함한 대화형 채팅
- Tool을 통한 자동 Phase 2 활성화
- 실제 사용 패턴

**추천 대상:** 프로덕션 통합 예제

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
from agentskills import read_instructions

# Tool을 통해 자동
response = await agent.invoke_async("web-research 스킬 사용해줘")

# 수동
instructions = read_instructions(skill.path)
# 토큰 비용: <5000 tokens per skill
```

### Phase 3: Resources (참조 시)
```python
from agentskills import read_resource

# instructions에서 참조된 특정 파일 로드
api_docs = read_resource(skill.skill_dir, "references/api-docs.md")
helper = read_resource(skill.skill_dir, "scripts/helper.py")
```

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

## 예제 출력

### progressive_disclosure_demo.py

```
============================================================
[PHASE 1] Phase 1: Discovery (Metadata Only)
============================================================

📂 스캔 중: /path/to/skills
⏳ metadata만 로드 중 (instructions와 resources 제외)...

✅ 2개 Skill discovery

1. 📦 web-research
   설명: 웹 검색과 분석을 통해 포괄적인 리서치 수행...
   📊 예상 토큰: ~95 tokens
   🔧 허용 도구: WebFetch, Grep
   📁 경로: /path/to/skills/web-research/SKILL.md

💡 Phase 1 총합: 2개 Skill에 대해 ~190 tokens
   평균: ~95 tokens/skill

============================================================
[PHASE 2] Phase 2: Activation (Load Instructions)
============================================================

🎯 Skill activation 중: web-research
📄 Instructions 로드 중: /path/to/SKILL.md
⏳ SKILL.md body 읽는 중 (frontmatter 제외)...

✅ Instructions 로드 완료!
   📊 크기: 4523 characters
   📊 예상 토큰: ~1130 tokens
   📊 줄 수: 89

💡 Phase 2: 활성화 시에만 1130 tokens 로드
   ✓ metadata는 Phase 1에서 이미 로드됨 (재로드 안함)
   ✓ Resources는 아직 로드 안됨 (Phase 3)

============================================================
[PHASE 3] Phase 3: Resources (Load on Demand)
============================================================

📁 scripts/ 디렉토리 발견:

   📄 scripts/search.py
      ⏳ 필요시 로드 중...
      ✅ 로드 완료: 2456 chars, ~614 tokens

💡 Phase 3: 1개 resource 로드
   총합: ~614 tokens
```

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

## 고급 사용법

### 커스텀 Tool 통합

```python
from strands import tool

@tool
def custom_tool():
    """사용자 정의 tool"""
    pass

agent = Agent(
    tools=[skill_tool, custom_tool],
    ...
)
```

### 스킬 resource 접근

```python
# Agent가 실행 중에 resource 요청 가능
if "API 문서 로드" in user_request:
    api_docs = read_resource(skill.skill_dir, "references/api-docs.md")
    # 컨텍스트에서 api_docs 사용
```

## 문제 해결

**Skill을 찾을 수 없음:**
- `skills/` 디렉토리가 존재하는지 확인
- 각 Skill에 YAML frontmatter가 있는 `SKILL.md` 파일이 있는지 확인

**Import 에러:**
- 패키지 설치: `pip install -e strands_agentskills/`
- Python 경로 확인

**Model 에러:**
- Bedrock용 AWS 자격증명 확인
- 또는 다른 모델 사용: `model="anthropic.claude-3-haiku-20240307-v1:0"`

## 더 알아보기

- [AgentSkills.io 표준 문서](https://agentskills.io/specification)
- [Strands SDK 문서](https://docs.strands.so)
- [메인 README](../README.md)
