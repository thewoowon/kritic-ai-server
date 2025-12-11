import os
import asyncio
from typing import List, Dict, Any
import httpx
import json
import re


class AnalysisService:
    """Service to run reality check analysis using multiple LLMs"""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")

    async def analyze(
        self,
        original_response: str,
        context: str | None,
        models: List[str]
    ) -> Dict[str, Any]:
        """Run complete analysis using selected models"""

        # Run analyses in parallel
        tasks = []
        if "gpt4" in models:
            tasks.append(self._analyze_with_gpt4(original_response, context))
        if "claude" in models:
            tasks.append(self._analyze_with_claude(original_response, context))
        if "gemini" in models:
            tasks.append(self._analyze_with_gemini(original_response, context))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Synthesize results
        result = self._synthesize_results(original_response, responses)
        return result

    async def _analyze_with_gpt4(
        self,
        original_response: str,
        context: str | None
    ) -> Dict[str, Any]:
        """Analyze using GPT-5 as a skeptical investor"""

        prompt = self._build_prompt(
            original_response,
            context,
            role="brutally honest business analyst and skeptical investor"
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-5-mini",
                        "messages": [
                            {"role": "system", "content": "You are a brutally honest business analyst and skeptical investor. You MUST respond with valid JSON only."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 4000,
                        "response_format": {"type": "json_object"}
                    }
                )
                data = response.json()
                return {
                    "model": "gpt4",
                    "response": data.get("choices", [{}])[0].get("message", {}).get("content", "")
                }
        except Exception as e:
            print(f"GPT-5 analysis failed: {e}")
            return {"model": "gpt4", "response": "", "error": str(e)}

    async def _analyze_with_claude(
        self,
        original_response: str,
        context: str | None
    ) -> Dict[str, Any]:
        """Analyze using Claude as a competitor analyst"""

        prompt = self._build_prompt(
            original_response,
            context,
            role="competitor analyst and market researcher"
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.anthropic_api_key,
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 2000,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ]
                    }
                )
                data = response.json()
                return {
                    "model": "claude",
                    "response": data.get("content", [{}])[0].get("text", "")
                }
        except Exception as e:
            print(f"Claude analysis failed: {e}")
            return {"model": "claude", "response": "", "error": str(e)}

    async def _analyze_with_gemini(
        self,
        original_response: str,
        context: str | None
    ) -> Dict[str, Any]:
        """Analyze using Gemini as a market researcher"""

        prompt = self._build_prompt(
            original_response,
            context,
            role="skeptical market researcher and financial analyst"
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.google_api_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.7,
                            "maxOutputTokens": 2000
                        }
                    }
                )
                data = response.json()
                return {
                    "model": "gemini",
                    "response": data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                }
        except Exception as e:
            print(f"Gemini analysis failed: {e}")
            return {"model": "gemini", "response": "", "error": str(e)}

    def _build_prompt(
        self,
        original_response: str,
        context: str | None,
        role: str
    ) -> str:
        """Build the analysis prompt"""

        context_text = f"\n\nUser's Original Question: {context}" if context else ""

        return f"""You are a {role} with 20+ years of experience. A user received this AI-generated response and wants brutal honesty about its validity:

AI RESPONSE TO ANALYZE:
"{original_response}"{context_text}

YOUR MISSION: Tear this apart with data-driven skepticism. Channel the energy of a seasoned VC who's seen 1000 pitches fail. Be constructively brutal.

RESPONSE FORMAT - You MUST respond with a valid JSON object with this EXACT structure:

{{
  "optimism_bias_score": <number 0-100>,
  "optimism_analysis": "<2-3 sentence sharp analysis of why this score>",
  "competitors": [
    {{
      "name": "<exact company/product name>",
      "url": "<actual website or google search URL>",
      "description": "<1 sentence: what they do and why they're a threat>",
      "market_position": "<specific metric or position, e.g., '$2B revenue', 'Market leader', '40% market share'>"
    }}
  ],
  "market_reality": {{
    "claimed_size": "<extract exact claim from AI response, or 'Not specified'>",
    "actual_size": "<real market size with source if possible, e.g., '$50B TAM (Gartner 2024)'>",
    "serviceable_market": "<realistic TAM/SAM you can actually capture>",
    "truth_bomb": "<2-3 sentences destroying inflated market assumptions>"
  }},
  "feasibility": {{
    "technical": {{
      "difficulty": "<Easy/Medium/Hard/Extremely Hard>",
      "reality": "<3-4 sentences on actual technical challenges, tech stack complexity, talent needed>",
      "time_to_mvp": "<realistic estimate with reasoning>",
      "underestimated_challenges": ["<specific challenge 1>", "<specific challenge 2>", "<specific challenge 3>"]
    }},
    "financial": {{
      "claimed_cost": "<extract from AI response or 'Not mentioned'>",
      "actual_cost": "<realistic cost breakdown>",
      "burn_rate": "<monthly burn estimate>",
      "runway_needed": "<minimum funding needed to reach profitability>",
      "hidden_costs": ["<cost 1 they forgot>", "<cost 2 they forgot>", "<cost 3 they forgot>"]
    }},
    "timeline": {{
      "ai_claim": "<extract timeline from AI response>",
      "reality": "<actual timeline with milestones>",
      "why_longer": "<explain the gap between fantasy and reality>"
    }}
  }},
  "risk_factors": [
    {{
      "category": "<Technical/Market/Financial/Legal/Operational>",
      "risk": "<specific risk>",
      "severity": "<Low/Medium/High/Critical>",
      "reality_check": "<2 sentences explaining why this will hurt>"
    }}
  ],
  "final_verdict": {{
    "score": <number 0-10>,
    "label": "<Dead on Arrival/Needs Major Rework/Possible with Pivots/Promising with Caveats/Solid Opportunity>",
    "reasoning": "<4-5 sentences of sharp, honest analysis. Start with the biggest red flag.>",
    "one_liner": "<brutal one-sentence truth>",
    "if_you_proceed": "<specific actionable advice IF they still want to try>"
  }}
}}

CRITICAL INSTRUCTIONS:
- Use REAL company names, REAL data, REAL URLs when mentioning competitors
- If you don't know exact numbers, say "Est. $XXM-XXM based on similar markets" - don't make up precision
- Find AT LEAST 3-5 competitors. If the idea is "unique", you're not looking hard enough
- Your job is NOT to encourage - it's to prevent failure. Be the harsh truth they need
- Every claim in the AI response should be scrutinized. What sounds easy probably isn't
- Focus on what will ACTUALLY stop them: money running out, competitors crushing them, tech not working
- Use specific examples: "Like how Quibi burned $1.75B in 6 months" not "Some startups fail"

Return ONLY the JSON object, no other text."""

    def _parse_json_response(self, response_text: str) -> Dict[str, Any] | None:
        """Extract and parse JSON from LLM response"""
        try:
            # Try direct JSON parse first
            return json.loads(response_text)
        except:
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
        return None

    def _synthesize_results(
        self,
        original_response: str,
        llm_responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize results from multiple LLMs into final output"""

        # Parse JSON responses
        parsed_responses = []
        for r in llm_responses:
            if isinstance(r, dict) and r.get("response"):
                parsed = self._parse_json_response(r["response"])
                if parsed:
                    parsed_responses.append(parsed)

        print(f"Successfully parsed {len(parsed_responses)} JSON responses from {len(llm_responses)} LLMs")

        # If we have valid JSON responses, merge them intelligently
        if parsed_responses:
            return self._merge_analyses(original_response, parsed_responses)

        # Fallback to basic analysis if JSON parsing failed
        return self._create_fallback_analysis(original_response)

    def _merge_analyses(self, original_response: str, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple JSON analyses into one comprehensive result"""

        # Average optimism scores
        optimism_scores = [a.get("optimism_bias_score", 65) for a in analyses if a.get("optimism_bias_score")]
        avg_optimism = sum(optimism_scores) // len(optimism_scores) if optimism_scores else 65

        # Collect all competitors (deduplicate by name)
        all_competitors = {}
        for analysis in analyses:
            for comp in analysis.get("competitors", []):
                if comp.get("name") and comp["name"] not in all_competitors:
                    all_competitors[comp["name"]] = comp

        # Get best market reality analysis (prefer one with most detail)
        market_reality = max(
            [a.get("market_reality", {}) for a in analyses],
            key=lambda x: len(str(x.get("truth_bomb", ""))),
            default={}
        )

        # Merge feasibility assessments (take most pessimistic/realistic)
        all_feasibility = [a.get("feasibility", {}) for a in analyses if a.get("feasibility")]
        merged_feasibility = all_feasibility[0] if all_feasibility else {}

        # Collect all risk factors
        all_risks = []
        for analysis in analyses:
            all_risks.extend(analysis.get("risk_factors", []))

        # Get final verdicts and average scores
        final_scores = [a.get("final_verdict", {}).get("score", 5) for a in analyses if a.get("final_verdict", {}).get("score")]
        avg_score = sum(final_scores) // len(final_scores) if final_scores else 5

        # Get the most detailed verdict reasoning
        best_verdict = max(
            [a.get("final_verdict", {}) for a in analyses],
            key=lambda x: len(str(x.get("reasoning", ""))),
            default={}
        )

        # Get optimism analysis from best response
        optimism_analysis = max(
            [a.get("optimism_analysis", "") for a in analyses],
            key=len,
            default="분석 결과 낙관적 편향이 감지되었습니다."
        )

        return {
            "optimism_bias_score": avg_optimism,
            "optimism_analysis": optimism_analysis,
            "competitors": list(all_competitors.values())[:8],  # Top 8 competitors
            "market_size_reality": {
                "claimed": market_reality.get("claimed_size", "명시되지 않음"),
                "actual": market_reality.get("actual_size", "추가 검증 필요"),
                "notes": market_reality.get("truth_bomb", "시장 규모는 신중한 검증이 필요합니다.")
            },
            "feasibility_assessment": {
                "technical": merged_feasibility.get("technical", {}).get("reality", "기술적 검증 필요"),
                "financial": merged_feasibility.get("financial", {}).get("actual_cost", "재무 요구사항이 과소평가되었을 수 있음"),
                "timeline": merged_feasibility.get("timeline", {}).get("reality", "타임라인이 낙관적으로 추정됨")
            },
            "risk_factors": [risk.get("risk", str(risk)) if isinstance(risk, dict) else risk for risk in all_risks[:8]],
            "final_verdict": {
                "score": avg_score,
                "reasoning": best_verdict.get("reasoning", f"종합 분석 결과 {avg_score}/10점입니다. 낙관 편향 {avg_optimism}/100 감지. 모든 가정을 신중히 검증하세요."),
                "one_liner": best_verdict.get("one_liner", "현실적인 검증이 필요합니다."),
                "if_you_proceed": best_verdict.get("if_you_proceed", "진행하신다면, 경쟁사 분석과 MVP 검증부터 시작하세요.")
            }
        }

    def _create_fallback_analysis(self, original_response: str) -> Dict[str, Any]:
        """Create basic analysis when JSON parsing fails"""
        return {
            "optimism_bias_score": 70,
            "optimism_analysis": "AI 응답 분석 중 일부 제한이 있었으나, 일반적으로 낙관적 편향이 감지됩니다.",
            "competitors": [
                {
                    "name": "시장 조사 필요",
                    "url": "https://www.google.com/search?q=competitors",
                    "description": "상세한 경쟁사 분석을 위해 추가 조사가 필요합니다.",
                    "market_position": "미확인"
                }
            ],
            "market_size_reality": {
                "claimed": "명시되지 않음",
                "actual": "추가 검증 필요",
                "notes": "시장 규모와 관련된 주장은 독립적인 검증이 필요합니다."
            },
            "feasibility_assessment": {
                "technical": "기술적 실현 가능성은 추가 검증이 필요합니다. 실제 구현에는 예상보다 많은 시간과 리소스가 소요될 수 있습니다.",
                "financial": "재무 요구사항이 과소평가되었을 가능성이 있습니다. MVP 개발부터 시장 진입까지 필요한 자금을 신중히 계산하세요.",
                "timeline": "타임라인 추정이 낙관적일 수 있습니다. 실제로는 2-3배 더 걸릴 수 있습니다."
            },
            "risk_factors": [
                "시장 경쟁이 예상보다 치열할 수 있음",
                "고객 획득 비용이 높을 수 있음",
                "규제 및 법적 문제 가능성",
                "기술적 복잡도 과소평가",
                "자금 요구사항이 상당할 수 있음"
            ],
            "final_verdict": {
                "score": 5,
                "reasoning": "분석 결과 이 아이디어는 중간 정도의 실현 가능성을 보입니다. 진행하기 전에 경쟁사 분석, 시장 검증, 기술적 타당성을 철저히 확인하는 것이 중요합니다.",
                "one_liner": "신중한 검증 없이는 진행하지 마세요.",
                "if_you_proceed": "최소한의 MVP로 시작하여 실제 사용자 피드백을 받고, 경쟁사를 면밀히 분석하세요."
            }
        }
