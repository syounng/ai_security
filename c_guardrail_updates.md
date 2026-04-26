# C. 가드레일의 경직성과 업데이트 어려움

## 1. 주제 설명

이 주제는 AI 서비스를 한 번 안전하게 만들어 끝내는 방식이 아니라, 바뀌는 공격과 사용 패턴에 맞춰 정책을 계속 고쳐야 한다는 문제를 다룬다.  
특히 에이전트형 AI는 웹, 문서, 메일, MCP 도구, 내부 API처럼 다양한 입력과 출력을 가지므로, 단순한 텍스트 필터만으로는 충분하지 않다.

주니어 DevOps/Infra 관점에서 보면, 이 문제는 "모델 자체"보다도 "운영 규칙과 배포 방식"에 가깝다.  
즉, 정책을 코드처럼 버전 관리하고, 테스트하고, 배포하고, 되돌릴 수 있어야 한다.

## 2. 최근 문제가 되고 있는 지점

- OpenAI는 prompt injection을 "evolving security challenge"라고 설명하고, 에이전트에서는 외부 콘텐츠가 모델 행동을 바꿀 수 있다고 경고한다. [링크](https://openai.com/safety/prompt-injections/)
- OpenAI의 에이전트 안전 가이드도 untrusted input, structured output, tool approvals, trace grading/evals를 함께 쓰라고 권장한다. [링크](https://platform.openai.com/docs/guides/agent-builder-safety)
- NIST는 2026년에 agentic AI ecosystem에 measurement probes를 넣는 흐름을 다루고 있고, agent security 표준 이니셔티브도 시작했다. [링크](https://www.nist.gov/news-events/events/2026/04/nist-information-technology-laboratory-ai-webinar-series-building) / [링크](https://www.nist.gov/node/1906621)
- NIST는 자동 benchmark evaluation의 best practice 초안까지 내면서, 평가 자체를 운영 가능한 형태로 다루기 시작했다. [링크](https://www.nist.gov/news-events/news/2026/01/towards-best-practices-automated-benchmark-evaluations)

## 3. 해커톤 요구사항과 맞닿는 점

- 기술적 완성도: 정책 변경, 테스트, 적용, 롤백까지 한 흐름으로 보여줄 수 있다.
- 창의성: 단순 방어가 아니라 "정책을 계속 진화시키는 운영 레이어"로 보이게 만들 수 있다.
- 활용 가능성: 실제 회사의 AI/내부 도구/보안 정책 관리에도 붙이기 쉽다.

## 4. 구현 방법 구상

MVP는 다음 4개 화면이면 충분하다.

1. 정책 편집기
   - "외부 문서에서 발견된 지시문은 무시" 같은 규칙을 텍스트나 YAML 형태로 작성
2. 시뮬레이션 실행
   - 샘플 입력을 넣으면 어떤 규칙이 걸렸는지 보여줌
3. 정책 diff와 배포
   - 수정 전후 차이를 보여주고, 버전 태그를 붙여 저장
4. 회귀 리포트
   - 막힌 공격, 실패한 케이스, 위험 점수를 한 번에 표시

데모는 "업무용 에이전트가 웹페이지를 읽다가 숨은 지시문에 끌려가는 장면"을 넣고,  
정책을 바꾼 뒤 같은 입력에서 차단되는 모습을 보여주면 된다.

## 5. 한 줄 추천

이 주제는 "AI용 정책 CI/CD"로 포장하면 DevOps 감각과 가장 잘 맞는다.

