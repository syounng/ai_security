# 해커톤 아이디어 리포트

기준 자료:
- [로컬 노트](/Users/soyoung/Downloads/새로운%20노트.txt)
- [추가 노트](/Users/soyoung/Downloads/텍스트-ED3CA0D4D906-1.txt)
- Google 문서는 공개 본문이 보이지 않아, 제목과 연동 맥락만 참고했고 실제 문제 정의는 로컬 노트를 중심으로 정리했다.

## 1. 원문이 말하는 핵심 문제

- AI가 텍스트 답변 도구에서 에이전트, 멀티모달 시스템, 물리적 로봇까지 확장되면서 공격 표면이 급격히 커지고 있다.
- 기존 안전장치는 한 번 만들어두면 끝나는 구조가 아니라, 계속 바뀌는 공격 기법에 맞춰 빠르게 업데이트되어야 한다.
- 단일 텍스트 필터만으로는 부족하고, 이미지, 오디오, 비디오, 외부 문서, 도구 호출, 로봇 액션까지 함께 봐야 한다.
- 공격자 관점의 자동화된 red-teaming과 취약점 발견이 중요하다.
- "완벽한 가드레일"은 없으므로, 관측 가능성, 정책 수정 가능성, 지속적 개선이 핵심이다.
- 물리 세계로 내려오는 순간, 잘못된 판단이 실제 안전 사고로 이어질 수 있다.
- 콘텐츠 진위성도 문제다. AI 생성물, 편집물, 출처 불명 자료를 신뢰할 수 있게 구분해야 한다.

## 2. 최근 주제 리스트

- Prompt injection과 에이전트 보안은 2025~2026년에도 가장 큰 이슈다. OpenAI는 prompt injection을 "evolving security challenge"로 설명했고, 에이전트용 방어 설계를 따로 다루고 있다.
- OWASP LLM Top 10 2025는 prompt injection, sensitive data disclosure, excessive agency, system prompt leakage 같은 위험을 정리했다.
- NIST는 2024년 GenAI profile과 2025년 ARIA 평가 프로그램을 통해, AI를 실제 환경에서 평가하고 관리하는 흐름을 강화하고 있다.
- 멀티모달 moderation은 텍스트뿐 아니라 이미지 입력까지 포함하는 방향으로 진화했다.
- 물리 AI와 로봇 안전은 DeepMind가 semantic, physical, operational safeguard를 묶은 다층 안전 구조로 설명한다.
- 콘텐츠 provenance와 authenticity는 C2PA Content Credentials, Adobe Content Authenticity, Google SynthID 같은 흐름으로 커지고 있다.
- deceptive behavior, sleeper agent 같은 "학습된 악성 행동"이 안전학습만으로 쉽게 지워지지 않을 수 있다는 점도 중요한 최근 주제다.

## 3. 문제별 해결 방향

### A. 에이전트/도구 호출형 AI의 prompt injection

- 문제: 외부 웹페이지, 문서, 이메일, 이미지 안의 지시문이 모델의 행동을 탈취한다.
- 해결: 입력을 "사용자 지시"와 "비신뢰 콘텐츠"로 분리하고, 도구 호출 전에는 정책 엔진이 side effect를 심사하게 만든다.
- 구현 포인트: 출처 태깅, tool-call 허용 규칙, 위험 액션은 사람 확인, 외부 텍스트는 요약 전용 모드로 처리.

### B. 멀티모달 안전

- 문제: 텍스트 필터만으로는 이미지, 오디오, 비디오에 숨어 있는 위험을 못 잡는다.
- 해결: 멀티모달 분류기와 OCR/ASR 파이프라인을 묶어, 모든 입력에 대해 동일한 안전 점검을 거친다.
- 구현 포인트: 이미지 속 지시문 탐지, 음성 명령과 배경 잡음 분리, 생성물 사후 검사, 위험 주제별 점수화.

### C. 가드레일의 경직성과 업데이트 어려움

- 문제: 규칙을 바꾸려면 재학습이 필요하거나 운영 중 반영이 느리다.
- 해결: 정책을 코드처럼 다루는 "policy compiler"를 둬서 룰 수정과 배포를 분리한다.
- 구현 포인트: 정책 버전 관리, 시뮬레이션 테스트, canary 적용, 실패 사례 자동 리포트.

### D. 로봇/물리 AI 안전

- 문제: 잘못된 인식이나 잘못된 액션이 실제 사고로 이어진다.
- 해결: 현재 세계 상태와 허용 가능한 행동을 함께 평가하는 action gate를 둔다.
- 구현 포인트: geofence, 속도/힘 제한, 금지 구역, 비상 정지, 위험도 상승 시 human-in-the-loop 전환.

### E. 콘텐츠 진위성

- 문제: 생성물과 편집물의 출처가 불명확하면 신뢰할 수 없다.
- 해결: provenance badge와 검증 가능한 메타데이터를 기본 제공한다.
- 구현 포인트: C2PA / Content Credentials 표시, AI 생성 여부, 편집 이력, 모델/버전 정보 노출.

### F. 자동 red-teaming과 평가

- 문제: 수동 테스트만으로는 공격이 너무 빨리 바뀌어 따라갈 수 없다.
- 해결: 공격 생성기, 취약점 재현기, 회귀 테스트를 묶은 자동 평가 시스템을 만든다.
- 구현 포인트: 공격 시나리오 라이브러리, 위험 카테고리별 점수, 패치 전후 비교, 보고서 자동 생성.

## 4. 해커톤에서 만들기 좋은 아이디어

### 추천안: `Adaptive AI Safety OS`

- 한 문장: AI 에이전트와 멀티모달 시스템을 대상으로 자동 red-teaming, 정책 수정, 런타임 가드레일, 감사 로그를 한 화면에서 다루는 "안전 운영 체제"를 만든다.
- 왜 좋은가: 원문에서 반복적으로 나온 문제를 하나의 제품으로 묶을 수 있고, 데모가 강하다.
- 차별점: 단순 필터가 아니라 "공격 발견 -> 정책 수정 -> 재평가 -> 배포"의 폐루프를 보여줄 수 있다.

### MVP 구성

- 입력: 텍스트, 이미지, 문서, 웹페이지, 간단한 도구 호출 시나리오
- 탐지: prompt injection, 민감 정보 유출, 과도한 권한 요청, 위험한 도구 호출
- 대응: 차단, 경고, 사람 승인 요청, 안전 요약으로 강등
- 결과: 리스크 리포트, 취약한 프롬프트/도구, 수정된 정책 diff, before/after 점수

### 데모 시나리오

- 여행/업무 에이전트가 웹페이지를 읽다가 숨은 지시문에 낚이는 장면을 먼저 보여준다.
- 같은 입력을 안전 OS에 통과시키면, 악성 지시를 분리하고 위험한 액션을 막는다.
- 마지막에 "어떤 규칙을 추가하면 더 안전해지는지"를 자동 제안하게 한다.

### 왜 혁신적으로 보이는가

- 보안 툴이 아니라 "AI 시스템의 운영 레이어"로 보이기 때문이다.
- 공격 탐지, 정책 편집, 런타임 통제를 한 번에 묶으면 제품성이 높아진다.
- 나중에 고객사별 온프레미스 배포나 특정 도메인용 특화 정책으로 확장하기 쉽다.

## 5. 대안 아이디어

- `Prompt Firewall for Agents`: 웹/문서/메일 입력을 신뢰도 기반으로 분류하고, tool-call 직전 액션을 차단하는 경량 보안 레이어.
- `Multimodal Red Team Copilot`: 이미지/오디오/비디오까지 넣으면 공격 시나리오와 취약점 리포트를 자동 생성하는 평가 도구.
- `Content Provenance Inspector`: AI 생성물과 편집물의 출처, 편집 이력, 워터마크, 신뢰도를 보여주는 검증 뷰어.

## 6. 참고한 최근 자료

- OpenAI, [Understanding prompt injections](https://openai.com/safety/prompt-injections/)
- OpenAI, [Safety in building agents](https://platform.openai.com/docs/guides/agent-builder-safety)
- OWASP GenAI Security Project, [LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- NIST, [AI RMF: Generative AI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence)
- NIST, [ARIA Pilot Evaluation Report](https://www.nist.gov/publications/assessing-risks-and-impacts-ai-aria-pilot-evaluation-report)
- Google DeepMind, [Responsibly advancing AI and robotics](https://deepmind.google/en/models/gemini-robotics/responsibly-advancing-ai-and-robotics/)
- Google DeepMind, [Gemini Robotics](https://deepmind.google/models/gemini-robotics/)
- C2PA, [Content Credentials](https://c2pa.org/)
- Adobe, [Content Authenticity beta](https://blog.adobe.com/en/publish/2025/04/24/adobe-content-authenticity-now-public-beta-helps-creators-secure-attribution)
- Anthropic, [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
