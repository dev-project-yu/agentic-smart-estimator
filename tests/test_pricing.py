import unittest

from pricing_engine import PricingEngine
from semantic_layer import SemanticLayer


class TestPricingEngine(unittest.TestCase):
    def test_duration_changes_quote(self):
        semantic_layer = SemanticLayer()
        pricing = PricingEngine(semantic_layer)
        analysis = {"complexity_score": 1.28}
        q1 = pricing.estimate(
            project_name="Demo Project",
            university_name="Sample University",
            requirement_summary="Need automation",
            selected_modules=["教务管理流程优化", "行政审批流程优化", "学生服务流程优化"],
            duration_months=1,
            analysis=analysis,
        )
        q3 = pricing.estimate(
            project_name="Demo Project",
            university_name="Sample University",
            requirement_summary="Need automation",
            selected_modules=["教务管理流程优化", "行政审批流程优化", "学生服务流程优化"],
            duration_months=3,
            analysis=analysis,
        )
        self.assertGreater(q1["final_quote_krw"], q3["final_quote_krw"])
        self.assertNotEqual(q1["final_quote_krw"], q3["final_quote_krw"])

    def test_repeated_inputs_are_deterministic(self):
        semantic_layer = SemanticLayer()
        pricing = PricingEngine(semantic_layer)
        analysis = {"complexity_score": 1.15}
        first = pricing.estimate(
            project_name="Repeated",
            university_name="University A",
            requirement_summary="repeat test",
            selected_modules=["教务管理流程优化", "现有系统集成"],
            duration_months=2,
            analysis=analysis,
        )
        second = pricing.estimate(
            project_name="Repeated",
            university_name="University A",
            requirement_summary="repeat test",
            selected_modules=["教务管理流程优化", "现有系统集成"],
            duration_months=2,
            analysis=analysis,
        )
        self.assertEqual(first["final_quote_krw"], second["final_quote_krw"])

    def test_team_capacity_must_cover_workload(self):
        semantic_layer = SemanticLayer()
        pricing = PricingEngine(semantic_layer)
        analysis = {"complexity_score": 1.5}
        q = pricing.estimate(
            project_name="Capacity Test",
            university_name="Test University",
            requirement_summary="cover workload test",
            selected_modules=["教务管理流程优化", "行政审批流程优化", "学生服务流程优化"],
            duration_months=7,
            analysis=analysis,
        )
        self.assertGreaterEqual(
            q["team_capacity_pm"],
            q["billable_workload_pm"],
            "Recommended team size must cover the delivery workload under the selected duration.",
        )

    def test_short_schedule_is_flagged_unfeasible_when_capacity_is_insufficient(self):
        semantic_layer = SemanticLayer()
        pricing = PricingEngine(semantic_layer)
        analysis = {"complexity_score": 1.9}
        q = pricing.estimate(
            project_name="Short Schedule Test",
            university_name="Test University",
            requirement_summary="tight schedule",
            selected_modules=["教务管理流程优化", "行政审批流程优化", "学生服务流程优化"],
            duration_months=2,
            analysis=analysis,
        )
        self.assertFalse(q["feasible"], "Short schedule should be marked infeasible if team capacity cannot cover the workload.")


if __name__ == "__main__":
    unittest.main()
