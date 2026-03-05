"""서버관리 AI 에이전트"""

from .base_agent import BaseAgent


class ServerAgent(BaseAgent):
    """서버 관리 및 인프라 지원 에이전트"""

    agent_type = "server"

    async def process(self, message: str, **kwargs) -> str:
        """서버 관련 메시지 처리"""
        clean_message = message
        for trigger in self.triggers:
            clean_message = clean_message.replace(trigger, "").strip()

        if not clean_message:
            clean_message = "서버 관련 도움이 필요하신가요? 어떤 내용을 도와드릴까요?"

        return await self.respond(clean_message, kwargs.get("history"))

    async def diagnose_issue(self, error_log: str) -> str:
        """서버 에러 진단"""
        prompt = f"""
다음 에러 로그를 분석하고 해결책을 제시해주세요:

```
{error_log}
```

분석 항목:
- 에러 원인
- 영향 범위
- 즉시 조치 사항
- 근본 해결 방안
- 재발 방지 대책
"""
        return await self.respond(prompt)

    async def deployment_checklist(self, service_name: str) -> str:
        """배포 체크리스트 생성"""
        prompt = f"""
'{service_name}' 서비스 배포를 위한 체크리스트를 작성해주세요.

포함 항목:
- 배포 전 점검 사항
- 배포 단계
- 롤백 계획
- 배포 후 확인 사항
- 모니터링 포인트
"""
        return await self.respond(prompt)

    async def security_audit(self, target: str) -> str:
        """보안 점검 가이드"""
        prompt = f"""
'{target}'에 대한 보안 점검 가이드를 작성해주세요.

점검 항목:
- 인증/인가 점검
- 네트워크 보안
- 데이터 보호
- 로깅/모니터링
- 취약점 체크리스트
"""
        return await self.respond(prompt)
