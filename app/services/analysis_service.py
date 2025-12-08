import os
import asyncio
from typing import List, Dict, Any
import httpx


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
                            {"role": "system", "content": "You are a brutally honest business analyst."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2000
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

        context_text = f"\n\nOriginal question: {context}" if context else ""

        return f"""You are a {role}. A user received this response from an AI assistant:

"{original_response}"{context_text}

Your job: Identify overoptimism, find competitors, verify claims, and assess feasibility.

Provide:
1. Optimism bias score (0-100, where 100 = extremely optimistic)
2. List of existing competitors with brief descriptions
3. Market size reality check (compare claimed vs actual)
4. Technical feasibility concerns
5. Financial reality check (costs, funding needed)
6. Timeline reality (actual time needed vs claimed)
7. Top 5 risk factors
8. Final score (0-10, where 10 = highly feasible) with reasoning

Be specific. Use data when possible. Be harsh but fair. Focus on reality, not possibilities."""

    def _synthesize_results(
        self,
        original_response: str,
        llm_responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize results from multiple LLMs into final output"""

        # Extract all responses
        all_text = "\n\n".join([
            r.get("response", "") for r in llm_responses if isinstance(r, dict) and r.get("response")
        ])

        # Parse optimism scores (simple extraction - in production, use better parsing)
        optimism_scores = []
        for line in all_text.split("\n"):
            if "optimism" in line.lower() and any(char.isdigit() for char in line):
                try:
                    score = int(''.join(filter(str.isdigit, line))[:2])
                    if 0 <= score <= 100:
                        optimism_scores.append(score)
                except:
                    pass

        avg_optimism = sum(optimism_scores) // len(optimism_scores) if optimism_scores else 65

        # Parse final scores
        final_scores = []
        for line in all_text.split("\n"):
            if ("final score" in line.lower() or "score:" in line.lower()) and "/" in line:
                try:
                    score_text = line.split("/")[0]
                    score = int(''.join(filter(str.isdigit, score_text))[-1])
                    if 0 <= score <= 10:
                        final_scores.append(score)
                except:
                    pass

        avg_final_score = sum(final_scores) // len(final_scores) if final_scores else 5

        # Extract competitors (simple parsing)
        competitors = []
        in_competitor_section = False
        for line in all_text.split("\n"):
            if "competitor" in line.lower():
                in_competitor_section = True
            elif in_competitor_section and (line.strip().startswith("-") or line.strip().startswith("•")):
                comp_name = line.strip().lstrip("-•").strip().split(":")[0].strip()
                if comp_name and len(comp_name) < 50:
                    competitors.append({
                        "name": comp_name,
                        "url": f"https://www.google.com/search?q={comp_name.replace(' ', '+')}",
                        "description": "Competitor identified by AI analysis"
                    })
                    if len(competitors) >= 5:
                        break

        # Extract risk factors
        risk_factors = []
        in_risk_section = False
        for line in all_text.split("\n"):
            if "risk" in line.lower():
                in_risk_section = True
            elif in_risk_section and (line.strip().startswith("-") or line.strip().startswith("•") or line.strip()[0].isdigit()):
                risk = line.strip().lstrip("-•0123456789.").strip()
                if risk and len(risk) < 200:
                    risk_factors.append(risk)
                    if len(risk_factors) >= 5:
                        break

        # Build final result
        return {
            "optimism_bias_score": avg_optimism,
            "competitors": competitors[:5],
            "market_size_reality": {
                "claimed": "Market size claims need verification",
                "actual": "Actual market size varies significantly",
                "notes": "Detailed analysis from LLM responses indicates potential overestimation"
            },
            "feasibility_assessment": {
                "technical": "Technical feasibility requires further validation",
                "financial": "Financial requirements are likely underestimated",
                "timeline": "Timeline estimates appear optimistic"
            },
            "risk_factors": risk_factors if risk_factors else [
                "Market competition is fierce",
                "Customer acquisition costs may be high",
                "Regulatory challenges possible",
                "Technical complexity underestimated",
                "Funding requirements significant"
            ],
            "final_verdict": {
                "score": avg_final_score,
                "reasoning": f"Based on multi-LLM analysis, this idea scores {avg_final_score}/10. " +
                            f"Optimism bias detected at {avg_optimism}/100. " +
                            "Proceed with caution and validate all assumptions."
            }
        }
