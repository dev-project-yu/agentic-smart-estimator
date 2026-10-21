from __future__ import annotations

import json
import os
from typing import Any, Dict, List

try:
    from google import genai
except ImportError:  # pragma: no cover
    genai = None


class AgentService:
    def __init__(self, semantic_layer, knowledge_graph, rag_service):
        self.semantic_layer = semantic_layer
        self.knowledge_graph = knowledge_graph
        self.rag_service = rag_service
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.client = None
        if self.api_key and genai is not None:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.client = None

    def _fallback_analysis(self, requirement: str, selected_modules: List[str], duration_months: int) -> Dict[str, Any]:
        complexity_score = 1.0
        if len(selected_modules) >= 4:
            complexity_score = 1.35
        elif len(selected_modules) >= 2:
            complexity_score = 1.18
        if "시스템" in requirement or "통합" in requirement or "integration" in requirement.lower():
            complexity_score += 0.15
        if "데이터" in requirement or "분석" in requirement or "analytics" in requirement.lower():
            complexity_score += 0.1

        modules = self.semantic_layer.get_project_modules(selected_modules)
        tasks = []
        for module in modules:
            tasks.append({
                "module": module["name"],
                "estimated_effort_pm": int(module["base_workload"] * (0.9 if duration_months >= 3 else 1.05)),
                "deliverables": module.get("deliverables", [])
            })

        return {
            "ai_mode": "rule_based_fallback",
            "project_objective": "PI 프로젝트를 통한 대학 내 공정 개선 및 운영 효율성 향상",
            "modules": selected_modules,
            "tasks": tasks,
            "complexity_score": round(complexity_score, 2),
            "complexity_label": "medium" if complexity_score < 1.5 else "high",
            "deliverables": [item for module in modules for item in module.get("deliverables", [])],
            "risk_assessment": "short_schedule_risk" if duration_months <= 2 else "normal_schedule",
            "knowledge_references": self.rag_service.retrieve(requirement, top_k=2),
            "graph_summary": self.knowledge_graph.get_graph_summary(),
            "workflow_steps": [
                "Requirement Analysis",
                "Knowledge Retrieval",
                "Workload Estimation",
                "Pricing Calculation",
                "Proposal Generation",
                "Validation"
            ],
        }

    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        if self.client is None:
            raise RuntimeError("Gemini client is not available.")
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={"temperature": 0.2, "top_p": 0.8, "max_output_tokens": 1200},
        )
        content = getattr(response, "text", None)
        if not content:
            raise RuntimeError("Empty Gemini response.")
        clean_text = content.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.strip("`")
            if clean_text.lower().startswith("json"):
                clean_text = clean_text[4:].strip()
        return json.loads(clean_text)

    def analyze_requirement(self, requirement: str, selected_modules: List[str], duration_months: int) -> Dict[str, Any]:
        retrieval = self.rag_service.retrieve(requirement, top_k=3)
        graph_summary = self.knowledge_graph.get_graph_summary()
        similar_projects = self.semantic_layer.get_similar_projects(selected_modules)
        fallback = self._fallback_analysis(requirement, selected_modules, duration_months)

        if not self.api_key or self.client is None:
            fallback["retrieval"] = retrieval
            fallback["similar_projects"] = similar_projects
            return fallback

        prompt = (
            "You are a PI project estimation assistant. Return only valid JSON with keys: "
            "project_objective, modules, tasks, complexity_score, complexity_label, "
            "deliverables, risk_assessment, reasons. "
            "Use the following requirement text and retrieval notes. "
            f"Requirement: {requirement}\n"
            f"Selected modules: {selected_modules}\n"
            f"Duration months: {duration_months}\n"
            f"Retrieval notes: {json.dumps(retrieval, ensure_ascii=False)}\n"
            f"Similar projects: {json.dumps(similar_projects[:2], ensure_ascii=False)}"
        )

        try:
            analysis = self._call_gemini(prompt)
            analysis["ai_mode"] = "gemini"
            analysis["retrieval"] = retrieval
            analysis["similar_projects"] = similar_projects
            analysis["graph_summary"] = graph_summary
            analysis["workflow_steps"] = [
                "Requirement Analysis",
                "Knowledge Retrieval",
                "Workload Estimation",
                "Pricing Calculation",
                "Proposal Generation",
                "Validation"
            ]
            return analysis
        except Exception as exc:  # pragma: no cover
            fallback["retrieval"] = retrieval
            fallback["similar_projects"] = similar_projects
            fallback["error"] = str(exc)
            return fallback
