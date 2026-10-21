from __future__ import annotations

import math
from typing import Any, Dict, List


class PricingEngine:
    def __init__(self, semantic_layer) -> None:
        self.semantic_layer = semantic_layer
        self.role_cost_map = {
            item["role"]: int(item["monthly_cost_krw"])
            for item in semantic_layer.get_cost_assumptions()["roles"]
        }
        self.role_weights = {
            "PM": 0.18,
            "BA": 0.22,
            "Developer": 0.32,
            "QA": 0.16,
            "UX": 0.07,
            "Data": 0.05,
        }

    @staticmethod
    def _format_krw(value: int) -> str:
        return f"₩{value:,.0f}"

    def _schedule_factor(self, duration_months: int) -> float:
        if duration_months <= 1:
            return 1.55
        if duration_months == 2:
            return 1.35
        if duration_months == 3:
            return 1.00
        if duration_months in (4, 5):
            return 0.92
        if duration_months == 6:
            return 0.85
        if duration_months == 7:
            return 0.78
        if duration_months == 12:
            return 0.70
        if duration_months > 7:
            return 0.75
        return 1.0

    def _utilization_rate(self, duration_months: int) -> float:
        if duration_months <= 2:
            return 0.60
        if duration_months <= 6:
            return 0.72
        return 0.75

    def _calculate_feasibility(self, total_billable_pm: float, duration_months: int, team_total_people: int) -> Dict[str, Any]:
        utilization = self._utilization_rate(duration_months)
        team_capacity_pm = team_total_people * duration_months * utilization
        feasible = team_capacity_pm >= total_billable_pm * 1.02
        if duration_months <= 2 and team_total_people >= 35:
            feasible = False
        if duration_months >= 7 and team_total_people >= 60:
            feasible = False
        if feasible:
            if duration_months <= 2:
                risk_label = "높음"
                note = "단기 일정은 높은 리스크가 있으며, 범위 조정이나 추가 검토를 권장합니다."
            elif duration_months <= 6:
                risk_label = "보통"
                note = "적정 범위의 일정으로 보이며, 자원 배치와 리스크 통제가 중요합니다."
            else:
                risk_label = "낮음"
                note = "장기 일정으로 자원 여력이 충분하여 안정적으로 수행 가능성이 높습니다."
            execution_status = "실행 가능"
        else:
            if duration_months <= 2:
                risk_label = "높음"
                note = "2개월 이하 일정은 필수 범위와 인력 구조를 재검토해야 하며, 현재 구성으로는 적용이 어렵습니다."
            elif duration_months <= 6:
                risk_label = "보통"
                note = "시스템 및 인력의 실제 적합성을 재검토할 필요가 있습니다. 현재 계획으로는 일정/인력 불균형이 발생합니다."
            else:
                risk_label = "높음"
                note = "주어진 기간과 팀 규모로는 실제 작업량을 커버할 수 없어 계획을 조정해야 합니다."
            execution_status = "불가"
        return {
            "team_capacity_pm": round(team_capacity_pm, 1),
            "utilization_rate": utilization,
            "feasible": feasible,
            "execution_status": execution_status,
            "risk_label": risk_label,
            "note": note,
        }

    def estimate(
        self,
        project_name: str,
        university_name: str,
        requirement_summary: str,
        selected_modules: List[str],
        duration_months: int,
        analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        module_data = self.semantic_layer.get_project_modules(selected_modules)
        base_workload_pm = float(sum(int(item["base_workload"]) for item in module_data))
        complexity_score = float(analysis.get("complexity_score", 1.0))
        adjusted_workload_pm = round(base_workload_pm * complexity_score, 1)
        schedule_factor = self._schedule_factor(duration_months)
        total_billable_pm = round(adjusted_workload_pm * schedule_factor, 1)

        required_roles = self.semantic_layer.get_required_roles(selected_modules)
        effective_utilization = self._utilization_rate(duration_months)
        total_people = max(1, math.ceil((total_billable_pm / max(duration_months * effective_utilization, 1)) * 1.02))
        team_heads = {}
        if required_roles:
            base_share = {role: self.role_weights.get(role, 0.1) for role in required_roles}
            normalized = sum(base_share.values())
            for role in required_roles:
                team_heads[role] = max(1, round((total_people * (base_share[role] / normalized))));
            current_total = sum(team_heads.values())
            while current_total < total_people:
                for role in required_roles:
                    if current_total >= total_people:
                        break
                    team_heads[role] += 1
                    current_total += 1
            while current_total > total_people:
                for role in reversed(required_roles):
                    if current_total <= total_people:
                        break
                    if team_heads[role] > 1:
                        team_heads[role] -= 1
                        current_total -= 1

        labor_cost = 0
        cost_breakdown = []
        for role, headcount in team_heads.items():
            monthly = self.role_cost_map.get(role, 9000000)
            role_total = headcount * monthly * duration_months
            labor_cost += role_total
            cost_breakdown.append({
                "role": role,
                "headcount": headcount,
                "monthly_cost_krw": monthly,
                "duration_months": duration_months,
                "total_cost_krw": role_total,
            })

        feasibility_info = self._calculate_feasibility(total_billable_pm, duration_months, total_people)

        management_cost = round(labor_cost * 0.12)
        risk_rate = 0.18 if duration_months <= 2 else 0.08 if duration_months <= 6 else 0.06
        risk_cost = round(labor_cost * risk_rate)
        subtotal = labor_cost + management_cost + risk_cost
        profit_margin = round(subtotal * 0.18)
        final_quote = subtotal + profit_margin

        if not feasibility_info["feasible"]:
            management_cost = round(labor_cost * 0.14)
            risk_cost = round(labor_cost * 0.22)
            subtotal = labor_cost + management_cost + risk_cost
            profit_margin = round(subtotal * 0.20)
            final_quote = subtotal + profit_margin

        return {
            "project_name": project_name,
            "university_name": university_name,
            "requirement_summary": requirement_summary,
            "duration_months": duration_months,
            "selected_modules": selected_modules,
            "base_workload_pm": round(base_workload_pm, 1),
            "adjusted_workload_pm": round(adjusted_workload_pm, 1),
            "schedule_factor": round(schedule_factor, 2),
            "billable_workload_pm": round(total_billable_pm, 1),
            "team_total_people": int(sum(team_heads.values())),
            "team_capacity_pm": round(feasibility_info["team_capacity_pm"], 1),
            "utilization_rate": round(feasibility_info["utilization_rate"], 2),
            "feasible": feasibility_info["feasible"],
            "feasibility": feasibility_info["note"],
            "execution_status": feasibility_info["execution_status"],
            "risk_level": feasibility_info["risk_label"],
            "risk_assessment": {
                "label": feasibility_info["risk_label"],
                "note": feasibility_info["note"],
            },
            "complexity_score": round(complexity_score, 2),
            "required_roles": required_roles,
            "team_headcount": team_heads,
            "cost_breakdown": cost_breakdown,
            "labor_cost_krw": labor_cost,
            "management_cost_krw": management_cost,
            "risk_cost_krw": risk_cost,
            "profit_margin_krw": profit_margin,
            "subtotal_krw": subtotal,
            "final_quote_krw": final_quote,
            "calculation_basis": [
                "기본 모듈 작업량 합계",
                "복잡도 계수 적용",
                "일정 압축/확장 계수 적용",
                "인력 활용률 = 팀 가용 인월 기반 계산",
                "관리비 + 위험 버퍼 + 이익률",
            ],
            "formatted_final_quote": self._format_krw(final_quote),
        }
