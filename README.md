# Strands Agent Skills

**Strands Agents SDK를 위한 Agent Skills 시스템**

Claude Code의 [Skills 패턴](https://www.claude.com/blog/skills-explained)을 Strands SDK에 구현한 두 가지 방식을 제공합니다.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📖 개요

### Agent Skills란?

Agent Skills는 AI Agent에게 도메인별 전문 지식과 작업 흐름을 제공하는 모듈형 시스템입니다:

- **전문 지식**: 특정 도메인(웹 리서치, 코드 리뷰 등)에 대한 상세한 가이드
- **구조화된 워크플로우**: 검증된 단계별 프로세스
- **모범 사례**: 도메인 전문가의 노하우를 캡슐화
- **재사용 가능**: 여러 프로젝트에서 공유 가능

### Skills 작동 방식

Claude Code와 동일하게, Skills는 3단계로 작동합니다:

#### 1️⃣ Discovery (시작 시)

Agent 시작 시 각 Skill의 **이름과 설명만** 로드합니다. 빠른 시작을 유지하면서 Agent가 각 Skill이 언제 관련될지 알 수 있습니다.

```
skills/web-research/
  name: "web-research"
  description: "Structured approach to conducting web research"
```

#### 2️⃣ Activation (요청 매칭 시)

사용자 요청이 Skill의 설명과 매칭되면, Agent는 **전체 SKILL.md를 context에 로드**합니다. Claude는 semantic similarity로 요청과 설명을 매칭합니다.

```
User: "Research quantum computing"
→ Agent: "web-research skill matches, reading SKILL.md..."
```

#### 3️⃣ Execution (사용)

Agent가 Skill의 instructions를 따라 작업을 수행하며, 필요시 bundled files나 scripts를 로드합니다.

```
Agent: Following web-research skill instructions:
1. Identify research goals
2. Conduct searches
3. Synthesize findings
```

---

## 📦 두 가지 구현

| 구현 | 디렉토리 | 코드량 | 특징 | 추천 대상 |
|------|---------|--------|------|----------|
| **⭐ Skills Middleware** | [`skills_middleware/`](skills_middleware/) | ~500 lines | 표준 구현 | **대부분의 사용자** |
| **🏗️ Advanced Skills** | [`agent_skills/`](agent_skills/) | ~1,500+ lines | 고급 기능 | 명시적 제어 필요시 |

### Skills Middleware (표준 구현)

Claude Code의 공식 패턴을 따르는 표준 구현입니다.

```python
from skills_middleware import SkillsMiddleware
from strands.agent import Agent
from strands.tools.read import read_file

# Middleware로 Skills 활성화
middleware = SkillsMiddleware(skills_dir="./skills")

# Agent가 자동으로 skill 활용
agent = Agent(
    tools=[read_file],  # Agent가 SKILL.md 읽기 위해 필요
    middlewares=[middleware]
)

# Model-invoked: Agent가 스스로 Skill 선택
result = agent("Research quantum computing trends")
```

**특징:**
- ✅ **Model-invoked**: Agent가 자동으로 Skill 선택
- ✅ **Progressive Disclosure**: 필요한 시점에만 로드
- ✅ **Claude Code 패턴**: 공식 구현과 동일한 방식
- ✅ 간단한 설정 (3 steps)
- ✅ 높은 Agent 자율성

👉 [Skills Middleware 문서](skills_middleware/README.md)

### Advanced Skills (고급 구현)

명시적 제어와 상태 관리가 필요한 경우를 위한 구현입니다.

```python
from agent_skills import SkillSystem, use_skill
from pathlib import Path

system = SkillSystem(Path("./skills"))
system.discover_skills()

agent = Agent(tools=[use_skill])

# Tool-based: 명시적 tool 호출
result = agent("Research quantum computing", skill_system=system)
```

**특징:**
- ✅ 명시적 상태 관리 (Registry)
- ✅ Skill 활성화 캐싱
- ✅ Sub-agent 격리 실행
- ✅ Tool 기반 명시적 호출

👉 [Advanced Skills 문서](agent_skills/README.md)

---

## 🎯 어떤 구현을 선택해야 할까요?

### 📊 비교

| 항목 | Skills Middleware | Advanced Skills |
|------|-------------------|-----------------|
| **작동 방식** | Model-invoked (자동) | Tool-based (명시적) |
| **Claude Code 패턴** | ✅ 완전 일치 | ⚠️ 커스텀 구현 |
| **Agent 자율성** | ✅ 높음 | ⚠️ 제한적 |
| **설정 복잡도** | ✅ 낮음 (3 steps) | ⚠️ 높음 (4+ steps) |
| **코드량** | 500 lines | 1,500+ lines |
| **상태 관리** | ❌ 없음 | ✅ Registry |
| **Sub-agent 격리** | ❌ 없음 | ✅ 있음 |

### 권장 선택

**→ 대부분의 경우 `skills_middleware` 사용을 권장합니다.**

- ✅ Claude Code의 공식 패턴
- ✅ Agent가 스스로 Skill 선택
- ✅ 더 간단하고 유지보수하기 쉬움

**`agent_skills`는 다음이 필요한 경우:**

- Skill 사용 추적이 중요
- Sub-agent 격리 실행 필요
- 명시적 제어 선호

---

## 🚀 빠른 시작

### Skills Middleware (권장)

**1. 설치**
```bash
pip install strands pyyaml
```

**2. Skill 생성**

`skills/web-research/SKILL.md`:
```markdown
---
name: web-research
description: Structured approach to conducting thorough web research
---

# Web Research Skill

## When to Use
- User asks to research a topic
- Need to gather information from sources

## How to Use

### Step 1: Identify Research Goals
Define what you're trying to learn...

### Step 2: Conduct Searches
Use available tools to search...

### Step 3: Synthesize Findings
Organize and summarize results...

## Best Practices
- Verify sources
- Cross-reference information
- Cite sources properly
```

**3. Agent 생성**
```python
from skills_middleware import SkillsMiddleware
from strands.agent import Agent
from strands.tools.read import read_file

middleware = SkillsMiddleware("./skills")
agent = Agent(
    tools=[read_file],  # Required for reading SKILL.md
    middlewares=[middleware]
)

# Agent automatically uses skills when appropriate
result = agent("Research the latest AI developments")
print(result.message)
```

### Advanced Skills

자세한 내용은 [agent_skills/README.md](agent_skills/README.md)를 참고하세요.

---

## 📚 How Skills Work (상세)

### Phase 1: Discovery

**시기**: Agent 초기화 시
**로드**: 메타데이터만 (~100 tokens/skill)

```python
middleware = SkillsMiddleware("./skills")
# Loads: name, description, paths for all skills
```

System Prompt에 주입되는 정보:
```
Available Skills:

### web-research
Structured approach to conducting web research
Read: /path/to/skills/web-research/SKILL.md

### code-review
Systematic code review with best practices
Read: /path/to/skills/code-review/SKILL.md
```

### Phase 2: Activation

**시기**: 요청이 Skill 설명과 매칭될 때
**로드**: 전체 SKILL.md (~5k tokens)

```
User: "Can you research quantum computing trends?"

Agent (internal):
1. Checks available skills in system prompt
2. "web-research" description matches "research" request
3. Uses read_file tool to load SKILL.md
4. SKILL.md content now in context
```

### Phase 3: Execution

**시기**: Activation 후
**로드**: Supporting files as needed

```
Agent (following SKILL.md instructions):
1. Identify research goals (from Step 1)
2. Conduct searches (from Step 2)
3. May access scripts/helper.py if referenced
4. Synthesize findings (from Step 3)
```

---

## 🏗️ Skill 작성 가이드

### SKILL.md 구조

```markdown
---
name: skill-name              # Required: lowercase, hyphens
description: Brief description # Required: what and when
allowed-tools: Read, Write    # Optional: pre-approved tools
model: claude-opus-4          # Optional: preferred model
---

# Skill Title

## Description
Detailed explanation of what this skill does.

## When to Use
- Scenario 1 where this applies
- Scenario 2 where this is helpful
- Keywords users might say

## How to Use

### Step 1: [First Action]
Clear instructions...

### Step 2: [Next Action]
More instructions...

### Step 3: [Final Action]
Completion steps...

## Best Practices
- Practice 1
- Practice 2

## Examples

### Example 1: [Scenario]
**User:** "example request"
**Approach:**
1. Step...
2. Step...
```

### 디렉토리 구조

```
skills/
├── web-research/
│   ├── SKILL.md              # Required
│   ├── scripts/              # Optional
│   │   └── helper.py
│   └── references/           # Optional
│       └── apis.md
└── code-review/
    └── SKILL.md
```

### 작성 팁

#### Description 작성

사용자가 자연스럽게 사용할 키워드를 포함하세요:

**Good:**
```yaml
description: Structured approach to conducting thorough web research, including search strategies and source verification
```

Agent가 "research", "search", "investigate" 등의 요청에 매칭합니다.

**Bad:**
```yaml
description: A skill for finding things online
```

너무 모호하여 매칭이 어렵습니다.

#### When to Use 작성

구체적인 시나리오를 나열하세요:

```markdown
## When to Use
- User asks to "research [topic]"
- User needs to "find information about [subject]"
- User wants to "investigate [question]"
```

---

## 🔍 주요 차이점

### 실행 방식

**Skills Middleware (Model-invoked):**
```
User Request
   ↓
Agent sees skills in system prompt
   ↓
Agent matches request to skill description
   ↓
Agent reads SKILL.md with read_file tool
   ↓
Agent follows instructions
   ↓
Result
```

**Advanced Skills (Tool-based):**
```
User Request
   ↓
Agent invokes use_skill tool
   ↓
Sub-agent created with SKILL.md
   ↓
Sub-agent executes
   ↓
Result returned to main agent
```

### 코드 구조

**Skills Middleware:** 단순
```
loader.py      (~260 lines) - SKILL.md 파싱
middleware.py  (~200 lines) - System prompt 주입
__init__.py    (~40 lines)  - API exports
```

**Advanced Skills:** 복잡
```
loader.py      - Filesystem operations
registry.py    - State management
executor.py    - Sub-agent creation
system.py      - Unified facade
tool.py        - Tool definitions
models.py      - Data models
utils/         - Utilities
```

---

## 📖 문서

### Skills Middleware
- [README](skills_middleware/README.md) - 전체 문서
- [Examples](skills_middleware/example.py) - 사용 예제
- [Tests](skills_middleware/test_basic.py) - 테스트

### Advanced Skills
- [README](agent_skills/README.md) - 전체 문서
- [Architecture](agent_skills/README.md#아키텍처) - 설계 상세

### 비교
- [COMPARISON](skills_middleware/COMPARISON.md) - 상세 비교 분석

---

## 📖 참고 자료

- [Claude Code: Skills Explained](https://www.claude.com/blog/skills-explained)
- [Strands Agents SDK](https://github.com/strands-ai/strands)
- [deepagents-cli](ref/deepagents/) - 참고 구현

---

## 🤝 기여

Issues와 PR을 환영합니다!

```bash
git clone https://github.com/yourusername/strands-agent-skills.git
cd strands-agent-skills

pip install -e .
pytest skills_middleware/test_basic.py -v
```

---

## 📄 라이선스

MIT License

---

## ❓ FAQ

**Q: 어떤 구현을 사용해야 하나요?**
A: 대부분 `skills_middleware`를 권장합니다. Claude Code의 표준 패턴이고 더 간단합니다.

**Q: Skills는 어떻게 작동하나요?**
A: Model-invoked 방식입니다. Agent가 system prompt의 skill 목록을 보고, 요청과 매칭되면 자동으로 SKILL.md를 읽어 사용합니다.

**Q: Skill이 자동으로 선택되지 않으면?**
A: Description을 사용자가 자연스럽게 사용할 키워드로 개선하세요. "research", "analyze" 등 동사를 포함하세요.

**Q: 두 구현의 SKILL.md 형식은 같나요?**
A: 네, 완전히 동일합니다. Skills를 재사용할 수 있습니다.

**Q: 성능 차이가 있나요?**
A: Skills Middleware는 메모리를 덜 사용하고, Advanced는 캐싱으로 재사용시 빠릅니다. 실제로는 거의 차이 없습니다.

---

**Happy Coding! 🎉**

*Start with `skills_middleware` - the standard way to use Skills with Strands SDK*
