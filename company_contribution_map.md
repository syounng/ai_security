# 세 회사 서비스 이해와 기여 지점

기준 질문:
- `AI 시스템의 정책을 수정하고`
- `공격 시나리오로 검증하고`
- `결과를 배포하는 가드레일`

이 흐름에서 내가 어디를 이해해야 하고, 어디를 고도화할 수 있는지 정리한 문서다.

## 1. 먼저 핵심 결론

- `AIM Intelligence`는 이 문제를 가장 직접적으로 제품화한 회사다.
- `AI-Nexus`는 보안 제품보다 `거버넌스/감사/문서화` 레이어에 가깝다.
- `cmux`는 보안 회사는 아니지만, `에이전트 오케스트레이션과 평가 실행 환경`을 잘 맞춰 주는 도구다.

즉, 네가 만들 C 주제는 세 회사에서 다음처럼 다르게 해석된다.

- AIM Intelligence: `실시간 guardrail + red teaming + 운영 대시보드`
- AI-Nexus: `AI risk management + compliance evidence + policy lifecycle`
- cmux: `agent evaluation harness + operator workflow + failure surfacing`

## 2. AIM Intelligence

### 회사가 실제로 하는 일

공식 페이지 기준으로 AIM Intelligence는 `AI security infrastructure`를 만든다.

- `Stinger`: `Auto-generate millions of attack scenarios`, `end-to-end agentic red teaming`, `attack across every modality`
- `Starfort`: `proxy-level blocking of malicious prompts`, `real-time masking of sensitive data`, `control abnormal API calls by autonomous agents`
- `AIM Supervisor`: `safety planning`, `development`, `modification`, `deployment`, `management`

참고:
- [AIM 공식 소개](https://www.aim-intelligence.com/en/company)
- [AIM 메인 페이지](https://www.aim-intelligence.com/)
- [AIM 블로그: MCP 공격](https://www.aim-intelligence.com/en/blog/exploiting-mcp)
- [AIM 블로그: Indirect Prompt Injection](https://www.aim-intelligence.com/blog/indirect-prompt-injection)
- [AIM 블로그: VLM safety](https://aim-intelligence.com/en/blog/elite-vlm-safety)

### 현재 구현 방식에서 읽히는 것

공식 설명에서 직접 확인되는 흐름은 아래와 같다.

1. `Stinger`가 공격 시나리오를 대량 생성한다.
2. 공격을 `commercial APIs`, `coding agents`, `text/image/audio/video/physical AI`에 적용한다.
3. 취약점, hallucination, 민감 정보 노출, 비정상 행동을 점검한다.
4. `Starfort`가 malicious prompt, sensitive data, abnormal API call을 runtime에서 차단한다.
5. `self-improving, policy-aware guardrails`와 `purple teaming`으로 운영 환경에 맞게 적응한다.

### 공개 자료에서 보이는 문제

- static rule만으로는 충분하지 않다. AIM은 스스로도 `Static rules break`라고 말한다. [AIM 메인 페이지](https://www.aim-intelligence.com/)
- prompt injection은 텍스트 필터만으로 해결되지 않고, tool output이나 external context로도 들어온다. [AIM MCP 글](https://www.aim-intelligence.com/en/blog/exploiting-mcp)
- multimodal/physical AI로 갈수록 단순 moderation은 한계가 커진다. [AIM 메인 페이지](https://www.aim-intelligence.com/)
- red teaming과 guardrail 사이를 한 번에 연결하는 운영 UX가 더 필요해 보인다. 공식 페이지는 `Unified Security Platform`, `One integration`, `complete lifecycle coverage`를 강조한다. [AIM 메인 페이지](https://www.aim-intelligence.com/)

### 네가 기여할 수 있는 부분

네 배경이 DevOps/Infra라면, AIM 쪽에서는 다음이 가장 자연스럽다.

- `policy diff / rollback / versioning`
- `evaluation harness automation`
- `attack result aggregation`
- `alerting and incident-style reporting`
- `deployment gating`

즉, 모델을 직접 만드는 것보다 `guardrail을 운영 가능한 시스템으로 만드는 쪽`에 기여 포인트가 있다.

### C 주제와의 연결

`C`는 사실 AIM의 제품 논리와 가장 가깝다.

- 정책을 수정한다.
- 공격 시나리오로 검증한다.
- 결과를 배포한다.

이 3단계가 이미 AIM의 `red teaming -> guardrail -> production` 서사와 맞는다.

## 3. AI-Nexus

### 회사가 실제로 하는 일

공식 페이지 기준으로 AI-Nexus는 `AI risk assessment`와 `compliance`에 중심이 있다.

- `Chief AI Officer as a Service`
- `AI risk assessments`
- `compliance audits`
- `mitigation strategies`
- `documentation support`
- `privacy compliance`

참고:
- [AI-Nexus About](https://www.ai-nexus.ai/about)
- [AI Risk Management Services](https://www.ai-nexus.ai/ai-risk-management-services)
- [AI Risk Management](https://www.ai-nexus.ai/ai-risk-management)
- [NIST AI RMF 페이지를 해설한 AI-Nexus 문서](https://www.ai-nexus.ai/AI-Risk-Management-Framework)

### 현재 구현 방식에서 읽히는 것

이 회사는 guardrail 엔진 자체보다는 `운영 체계`를 제공하는 쪽에 가깝다.

1. AI 시스템을 식별한다.
2. 데이터 흐름과 리스크를 분류한다.
3. 규제/정책/문서를 정렬한다.
4. mitigation plan과 audit evidence를 만든다.
5. monitoring과 continuous oversight를 붙인다.

공식 문서에서도 `governance`, `documentation`, `continuous monitoring`, `risk scoring`, `audit-ready framework`를 반복해서 강조한다.

### 공개 자료에서 보이는 문제

- 실제 기업은 AI를 빨리 배포하지만, 문서와 통제가 그 속도를 못 따라간다. [AI-Risk Management Services](https://www.ai-nexus.ai/ai-risk-management-services)
- compliance는 한 번 맞추면 끝이 아니라 계속 바뀌는 규제에 맞춰 업데이트해야 한다. [AI-Risk Management Services](https://www.ai-nexus.ai/ai-risk-management-services)
- 공격 탐지보다 `증빙 가능한 리스크 관리`가 더 중요하다. [About](https://www.ai-nexus.ai/about)

### 네가 기여할 수 있는 부분

AI-Nexus에서는 다음이 네 역할과 잘 맞는다.

- `risk report generator`
- `policy checklist / control mapping`
- `evidence pipeline`
- `audit trail automation`
- `monitoring dashboard`

즉, 보안 알고리즘 자체보다 `운영 증빙과 통제 자료를 자동화`하는 쪽이 기여 포인트다.

### E 주제와의 연결

`E`는 AI-Nexus와 특히 잘 맞는다.

- provenance
- authenticity
- documentation
- auditability

이건 AI-Nexus의 `compliance`와 `documentation support`에 거의 그대로 들어간다.

## 4. cmux

### 회사가 실제로 하는 일

cmux는 보안 회사가 아니라 `AI coding agent용 macOS terminal`을 만든다.

- vertical tabs
- notification rings
- split panes
- embedded browser
- socket API
- CLI automation

참고:
- [cmux 메인 페이지](https://www.cmux.dev/)
- [Getting Started](https://www.cmux.dev/docs/getting-started)
- [Concepts](https://www.cmux.dev/docs/concepts)

### 현재 구현 방식에서 읽히는 것

cmux는 여러 agent를 병렬로 돌리고, 그 상태를 사람이 보기 좋게 정리하는 데 초점이 있다.

1. workspace와 pane을 나눈다.
2. agent나 터미널 세션을 여러 개 띄운다.
3. notify ring으로 attention 필요한 세션을 강조한다.
4. socket/CLI로 자동화한다.

이 구조는 실제로 `agent orchestration`과 `evaluation harness` 만들기에 좋다.

### 공개 자료에서 보이는 문제

- 여러 agent를 동시에 돌리면 상태 추적이 어렵다.
- 작업이 꼬이면 어디서 실패했는지 보기 힘들다.
- coding agent, browser, terminal을 한 화면에서 다루는 운영 UX가 중요하다.

### 네가 기여할 수 있는 부분

cmux는 네가 만들 C/F 아이디어를 `운영 화면`으로 바꾸는 데 유용하다.

- `batch eval runner`
- `agent failure dashboard`
- `workspace-level run summaries`
- `red-team session launcher`
- `notification rules`

즉, cmux는 보안 제품 그 자체보다 `보안/평가 자동화가 돌아가는 작업대`를 만드는 쪽에 적합하다.

### F 주제와의 연결

`F`를 cmux 스타일로 풀면 아주 자연스럽다.

- 공격 프롬프트를 여러 agent에 병렬 실행
- 성공/실패를 비교
- 위험 행동을 알림으로 띄움
- 결과를 CLI에서 바로 리포트

이건 사실상 `LLM evaluation harness`에 가깝다.

## 5. 다른 회사에서 배울 수 있는 패턴

### OpenAI

OpenAI는 prompt injection을 layered defense로 다룬다.

- model training
- monitoring
- security protections
- red-teaming
- user confirmations

참고:
- [Understanding prompt injections](https://openai.com/safety/prompt-injections/)
- [Safety in building agents](https://platform.openai.com/docs/guides/agent-builder-safety)
- [Advancing red teaming with people and AI](https://openai.com/index/advancing-red-teaming-with-people-and-ai/)

여기서 배울 점은, guardrail은 하나의 필터가 아니라 `여러 겹의 통제`로 설계된다는 것이다.

### Anthropic

Anthropic은 agent를 만들 때 `simple, composable patterns`를 강조하고, guardrails와 evals를 서로 다른 레이어로 둔다.

참고:
- [Building Effective AI Agents](https://www.anthropic.com/research/building-effective-agents/)

배울 점은, 복잡한 AI safety 제품도 처음부터 거대한 프레임워크로 시작하기보다 `단순한 workflow + programmatic checks`로 시작하는 편이 낫다는 것이다.

### C2PA / Adobe

콘텐츠 진위성은 `provenance`, `Content Credentials`, `inspect` 중심으로 구현된다.

참고:
- [C2PA](https://c2pa.org/)
- [Content Authenticity Initiative](https://contentauthenticity.org/)
- [How it works](https://contentauthenticity.org/how-it-works)
- [Adobe Content Authenticity](https://helpx.adobe.com/creative-cloud/help/cai/adobe-content-authenticity.html)

이쪽은 `E`를 이해할 때 도움이 된다. 파일에 출처와 편집 이력을 붙여서 `검증 가능한 신뢰`를 만드는 방식이다.

## 6. 네가 실제로 잡을 수 있는 기여 포인트

네가 지금 당장 설계할 수 있는 기여는 모델 연구가 아니라 `운영 가능성` 쪽이다.

1. `정책 관리`
   - policy as code
   - versioning
   - rollback
2. `공격 검증`
   - red-team scenario runner
   - scheduled eval
   - failure clustering
3. `배포/관측`
   - production gating
   - alerting
   - evidence log
4. `신뢰/진위`
   - provenance checks
   - inspect view
   - audit export

이 4개는 AIM, AI-Nexus, cmux 모두에서 형태만 다르게 필요하다.

## 7. 추천 우선순위

- `AIM Intelligence` 쪽은 `C`와 `F`에 가장 직접적으로 닿는다.
- `AI-Nexus` 쪽은 `E`와 `C`의 문서화/거버넌스 레이어에 닿는다.
- `cmux` 쪽은 `F`를 돌리는 작업 환경과 운영 UX에 닿는다.

즉, 네가 만들 서비스는 "모델을 더 똑똑하게"가 아니라 "AI 시스템을 더 운영 가능하게" 만드는 쪽으로 잡는 게 맞다.
