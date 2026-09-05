"""Service for handling Copilot queries."""

import os
import json
import httpx
from typing import Dict, Any

from backend.app.copilot.schemas import CopilotQueryRequest, CopilotQueryResponse
from backend.app.copilot.context import CopilotContextBuilder
from backend.app.copilot.prompts import COPILOT_SYSTEM_PROMPT, build_copilot_prompt
from backend.app.domain.finance_rules import DEFAULT_CURRENCY

class CopilotService:
    def __init__(self):
        self.context_builder = CopilotContextBuilder()
        self.api_key = os.environ.get("AI_API_KEY")
        self.provider = os.environ.get("AI_PROVIDER", "mock")
        self.model = os.environ.get("AI_MODEL", "mock-model")

    def query(self, request: CopilotQueryRequest) -> CopilotQueryResponse:
        # 1. Build authoritative context
        context = self.context_builder.build_context(request.question, request.exception_id)
        
        if "error" in context:
            return CopilotQueryResponse(
                answer=f"I cannot answer that right now: {context['error']}",
                supporting_data={},
                source_sections=[],
                confidence="N/A",
                requires_human_review=False
            )
            
        if "error" in context.get("data", {}):
            return CopilotQueryResponse(
                answer=f"I cannot answer that right now: {context['data']['error']}",
                supporting_data={},
                source_sections=context.get("source", []),
                confidence="N/A",
                requires_human_review=False
            )

        # 2. Check if we need to use deterministic fallback
        if self.provider == "mock" or not self.api_key or context.get("intent") == "general_summary":
            return self._deterministic_fallback(request.question, context)

        # 3. Call real LLM
        return self._call_llm(request.question, context)
        
    def _call_llm(self, question: str, context: Dict[str, Any]) -> CopilotQueryResponse:
        from backend.app.ai.resolver import LLMProvider
        provider = LLMProvider()
        if provider.is_mock():
            return self._deterministic_fallback(question, context)
            
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import SystemMessage, HumanMessage
            
            if provider.provider == "gemini":
                llm = ChatGoogleGenerativeAI(
                    model=provider.model,
                    google_api_key=provider.api_key,
                    temperature=0.1
                )
            else:
                return self._deterministic_fallback(question, context)
                
            prompt = build_copilot_prompt(question, context["data"])
            res = llm.invoke([
                SystemMessage(content=COPILOT_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ])
            answer_text = res.content
            
            requires_review = context["intent"] == "exception_investigation"
            return CopilotQueryResponse(
                answer=answer_text,
                supporting_data=context["data"],
                source_sections=context["source"],
                confidence="HIGH" if not requires_review else "MEDIUM",
                requires_human_review=requires_review
            )
        except Exception as e:
            print(f"Copilot LLM Error: {e}")
            return self._deterministic_fallback(question, context)

    def _format_currency(self, amount: float) -> str:
        return f"₹{amount:,.2f}"

    def _deterministic_fallback(self, question: str, context: Dict[str, Any]) -> CopilotQueryResponse:
        """Fallback when no LLM API key exists. Answers based strictly on intent."""
        
        intent = context.get("intent", "unknown")
        data = context.get("data", {})
        
        answer = "I don't have enough data in the current reconciliation run to answer that."
        requires_review = False
        confidence = "HIGH"

        if intent == "cash_position":
            metrics = data.get("cash_metrics", {})
            bank_cash = self._format_currency(metrics.get("bank_cash", 0))
            pending = self._format_currency(metrics.get("pending_settlement", 0))
            at_risk = self._format_currency(metrics.get("cash_at_risk", 0))
            expected = self._format_currency(metrics.get("gateway_net_expected", 0))
            
            answer = (
                f"**Current Cash Position**\n\n"
                f"• **Bank Cash:** {bank_cash}\n"
                f"• **Gateway Expected Net:** {expected}\n"
                f"• **Pending Settlement:** {pending}\n"
                f"• **Cash at Risk:** {at_risk}\n\n"
                f"Source: Phase 8 Cash Position"
            )
            
        elif intent == "forecast":
            forecast = data.get("forecast_7_day", [])
            if forecast:
                lines = []
                for day in forecast:
                    inflow = self._format_currency(day.get("expected_inflow", 0))
                    lines.append(f"• **{day.get('date')}:** {inflow}")
                answer = "**7-Day Deterministic Cash Forecast**\n\n" + "\n".join(lines)
            else:
                answer = "There are no future expected cash inflows scheduled in the deterministic dataset."
                
        elif intent == "exception_investigation":
            exc = data.get("exception_details", {})
            ai_rec = data.get("ai_recommendation", {})
            
            if exc:
                exc_type = exc.get("type", "UNKNOWN")
                diff = self._format_currency(exc.get("difference", 0))
                
                answer = (
                    f"**Exception Details ({exc.get('reconciliation_id')})**\n\n"
                    f"• **Type:** {exc_type}\n"
                    f"• **Difference:** {diff}\n"
                    f"• **Explanation:** {exc.get('explanation', 'N/A')}\n"
                )
                
                if ai_rec:
                    answer += (
                        f"\n**AI Recommendation (Phase 7)**\n"
                        f"• **Decision:** {ai_rec.get('decision')}\n"
                        f"• **Reasoning:** {ai_rec.get('reasoning')}\n"
                    )
                
                requires_review = True
                confidence = "MEDIUM" if ai_rec else "HIGH"
                
        elif intent == "reconciliation_summary":
            fin = data.get("financial_summary", {})
            counts = data.get("counts", {})
            
            reconciled = self._format_currency(fin.get("expected_settlement", 0) - fin.get("unreconciled_value", 0))
            
            answer = (
                f"**Reconciliation Summary**\n\n"
                f"• **Transactions Processed:** {counts.get('total', 0)}\n"
                f"• **Resolved:** {counts.get('resolved', 0)}\n"
                f"• **Unresolved:** {counts.get('unresolved', 0)}\n"
                f"• **Value Reconciled:** {reconciled}\n"
            )
            
        elif intent == "policy":
            policies = data.get("policies", [])
            answer = "**Policy Knowledge Retrieval:**\n\n"
            if policies:
                for p in policies:
                    answer += f"- {p[:200]}...\n"
            else:
                answer += "No matching policies found."
                
        elif intent == "historical":
            history = data.get("historical_cases", [])
            answer = "**Historical Cases Retrieval:**\n\n"
            if history:
                for h in history:
                    answer += f"- {h[:200]}...\n"
            else:
                answer += "No matching historical cases found."

        elif intent == "general_summary":
            metrics = data.get("cash_metrics", {})
            fin = data.get("financial_summary", {})
            
            answer = (
                f"I'm sorry, I couldn't understand your specific question. Here is a general summary:\n\n"
                f"• **Bank Cash:** {self._format_currency(metrics.get('bank_cash', 0))}\n"
                f"• **Value Reconciled:** {self._format_currency(fin.get('expected_settlement', 0) - fin.get('unreconciled_value', 0))}\n"
                f"• **Pending Settlement:** {self._format_currency(metrics.get('pending_settlement', 0))}\n"
            )
            confidence = "LOW"

        return CopilotQueryResponse(
            answer=answer,
            supporting_data=data,
            source_sections=context.get("source", []),
            confidence=confidence,
            requires_human_review=requires_review
        )

copilot_service = CopilotService()
