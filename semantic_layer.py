from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class SemanticLayer:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent
        self.data_dir = self.base_dir / "data"
        self.modules = self._load_json("modules.json").get("modules", [])
        self.projects = self._load_json("mock_projects.json").get("projects", [])
        self.roles = self._load_json("personnel_costs.json").get("roles", [])
        self.outcomes = self._load_json("outcomes.json").get("outcomes", [])

    def _load_json(self, filename: str) -> Dict[str, Any]:
        path = self.data_dir / filename
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def get_project_modules(self, selected_names: List[str] | None = None) -> List[Dict[str, Any]]:
        if selected_names:
            lookup = {module["name"]: module for module in self.modules}
            ordered = []
            for name in selected_names:
                if name in lookup:
                    ordered.append(lookup[name])
            return ordered
        return self.modules

    def get_module_workload(self, module_name: str) -> int:
        for module in self.modules:
            if module["name"] == module_name:
                return int(module["base_workload"])
        return 0

    def get_required_roles(self, module_names: List[str] | None = None) -> List[str]:
        module_names = module_names or [module["name"] for module in self.modules]
        role_set = set()
        for module in self.modules:
            if module["name"] in module_names:
                role_set.update(module.get("required_roles", []))
        return sorted(role_set)

    def get_task_dependencies(self, module_names: List[str] | None = None) -> List[Dict[str, str]]:
        items: List[Dict[str, str]] = []
        selected = set(module_names or [module["name"] for module in self.modules])
        for module in self.modules:
            if module["name"] in selected:
                for dep in module.get("dependencies", []):
                    dep_name = next((m["name"] for m in self.modules if m["id"] == dep), dep)
                    items.append({"from": dep_name, "to": module["name"], "type": "DEPENDS_ON"})
        return items

    def get_similar_projects(self, module_names: List[str], top_n: int = 3) -> List[Dict[str, Any]]:
        selected = set(module_names)
        scored_projects = []
        for project in self.projects:
            overlaps = len(set(project.get("module_ids", [])) & set(module_names))
            if overlaps == 0:
                continue
            score = overlaps * 3 + project.get("duration_months", 0)
            scored_projects.append({"project": project, "score": score})
        scored_projects.sort(key=lambda item: item["score"], reverse=True)
        return [item["project"] for item in scored_projects[:top_n]]

    def get_cost_assumptions(self) -> Dict[str, Any]:
        return {
            "management_rate": 0.12,
            "profit_rate": 0.18,
            "risk_buffer_rate": 0.08,
            "roles": self.roles,
            "schedule_policy": {
                "1": "compressed schedule with significant risk",
                "2": "high schedule pressure",
                "3": "balanced delivery target",
                "6": "extended timeline with lower risk"
            },
        }

    def get_outcomes(self, module_names: List[str] | None = None) -> List[Dict[str, Any]]:
        if not module_names:
            return self.outcomes
        selected = set(module_names)
        return [item for item in self.outcomes if item["name"] in selected]
