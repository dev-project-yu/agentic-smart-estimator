from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

st.set_page_config(page_title="PI Agentic Quote", page_icon="📊", layout="wide")

from agent_service import AgentService
from knowledge_graph import KnowledgeGraph
from pricing_engine import PricingEngine
from rag_service import RAGService
from semantic_layer import SemanticLayer

load_dotenv()


@st.cache_resource
def build_services():
    semantic_layer = SemanticLayer()
    knowledge_graph = KnowledgeGraph(semantic_layer)
    rag_service = RAGService()
    agent_service = AgentService(semantic_layer, knowledge_graph, rag_service)
    pricing_engine = PricingEngine(semantic_layer)
    return semantic_layer, knowledge_graph, rag_service, agent_service, pricing_engine


semantic_layer, knowledge_graph, rag_service, agent_service, pricing_engine = build_services()


def format_krw(value: int | float) -> str:
    return f"₩{value:,.0f}"


def render_markdown_quote(quote: dict, analysis: dict) -> str:
    lines = []
    lines.append("# PI 성과 기반 Agentic 견적서")
    lines.append("")
    lines.append(f"- 프로젝트명: {quote['project_name']}")
    lines.append(f"- 대학/기관: {quote['university_name']}")
    lines.append(f"- 선택 기간: {quote['duration_months']}개월")
    lines.append(f"- 최종 견적: {format_krw(quote['final_quote_krw'])}")
    lines.append("")
    lines.append("## 1. 프로젝트 요약")
    lines.append(quote["requirement_summary"])
    lines.append("")
    lines.append("## 2. 프로젝트 목표")
    lines.append(analysis.get("project_objective", "PI 기반 프로세스 혁신과 업무 효율 향상"))
    lines.append("")
    lines.append("## 3. 범위")
    for module in quote["selected_modules"]:
        lines.append(f"- {module}")
    lines.append("")
    lines.append("## 4. 작업량 및 인력 구성")
    lines.append(f"- 기초 작업량: {quote['base_workload_pm']} 인월")
    lines.append(f"- 계산 작업량: {quote['billable_workload_pm']} 인월")
    lines.append(f"- 팀 총 인원: {quote['team_total_people']}명")
    lines.append(f"- 팀 제공 인월: {quote['team_capacity_pm']} 인월")
    for role, count in quote["team_headcount"].items():
        lines.append(f"- {role}: {count}명")
    lines.append("")
    lines.append("## 5. 비용 내역")
    for item in quote["cost_breakdown"]:
        lines.append(f"- {item['role']}: {format_krw(item['total_cost_krw'])}")
    lines.append(f"- 관리비: {format_krw(quote['management_cost_krw'])}")
    lines.append(f"- 위험버퍼: {format_krw(quote['risk_cost_krw'])}")
    lines.append(f"- 이익: {format_krw(quote['profit_margin_krw'])}")
    lines.append(f"- 최종 견적: {format_krw(quote['final_quote_krw'])}")
    lines.append("")
    lines.append("## 6. 위험 및 가정")
    lines.append(quote["risk_assessment"]["note"])
    lines.append("")
    lines.append("## 7. 견적 계산 근거")
    for basis in quote["calculation_basis"]:
        lines.append(f"- {basis}")
    lines.append("")
    lines.append("## 8. RAG 참고 근거")
    for item in analysis.get("retrieval", [])[:3]:
        lines.append(f"- {item['title']} ({item['score']}): {item['snippet']}")
    return "\n".join(lines)


st.title("인스파이어파트너스 · PI Agentic 스마트 견적서")
st.caption("Synthetic / Mock Data 기반 데모. 실제 대학 프로젝트 정보가 아닌 시뮬레이션 데이터로 운영됩니다.")

with st.sidebar:
    st.subheader("프로젝트 설정")
    university_name = st.text_input("대학명", value="서울대학교")
    project_name = st.text_input("프로젝트명", value="PI 디지털 업무혁신")
    requirement_text = st.text_area(
        "프로젝트 요구사항",
        value=(
            "교무 행정, 관리자 승인, 학생 서비스 프로세스를 통합하고, "
            "기존 시스템과 연결하여 승인 시간을 줄이고 운영 효율성을 높이고 싶습니다."
        ),
        height=200,
    )
    module_names = [item["name"] for item in semantic_layer.get_project_modules()]
    module_display_names = {
        "教务管理流程优化": "교무 행정 프로세스 최적화",
        "行政审批流程优化": "관리자 승인 프로세스 최적화",
        "学生服务流程优化": "학생 서비스 프로세스 최적화",
        "现有系统集成": "기존 시스템 통합",
        "绩效分析与仪表板": "성과 분석 및 대시보드",
        "流程培训与知识转移": "프로세스 교육 및 지식 전이",
    }
    selected_modules = st.multiselect(
        "기능 모듈 선택",
        module_names,
        default=["教务管理流程优化", "行政审批流程优化", "学生服务流程优化"],
        format_func=lambda value: module_display_names.get(value, value),
    )
    duration_months = st.number_input("프로젝트 기간(개월)", min_value=1, max_value=12, value=3, step=1)
    generate = st.button("견적 생성", type="primary")

if generate:
    analysis = agent_service.analyze_requirement(requirement_text, selected_modules, int(duration_months))
    quote = pricing_engine.estimate(
        project_name=project_name,
        university_name=university_name,
        requirement_summary=requirement_text,
        selected_modules=selected_modules,
        duration_months=int(duration_months),
        analysis=analysis,
    )
    st.session_state.analysis = analysis
    st.session_state.quote = quote
else:
    st.session_state.setdefault("analysis", {})
    st.session_state.setdefault("quote", None)

analysis = st.session_state.get("analysis", {})
quote = st.session_state.get("quote")

if quote:
    left, right = st.columns([1.2, 1.8])
    with left:
        st.subheader("프로젝트 분석")
        st.write(analysis.get("project_objective", "PI 기반 프로세스 혁신 및 업무 효율 최적화"))
        st.markdown("**복잡도:** " + str(analysis.get("complexity_score", 1.0)))
        st.markdown("**위험 상태:** " + quote["risk_assessment"]["label"])
        st.markdown("**사업 검증:** " + quote["feasibility"])
        st.write("**기초 작업량:**", f"{quote['base_workload_pm']} 인월")
        st.write("**계산 작업량:**", f"{quote['billable_workload_pm']} 인월")
        st.write("**팀 총 인원:**", f"{quote['team_total_people']}명")
        st.write("**팀 제공 인월:**", f"{quote['team_capacity_pm']} 인월")
        st.write("**실행 판정:**", quote["execution_status"])
        st.write("**인력 구성:**")
        for role, count in quote["team_headcount"].items():
            st.write(f"- {role}: {count}명")

    with right:
        st.subheader("최종 견적")
        st.metric("최종 견적", format_krw(quote["final_quote_krw"]))
        st.metric("선택 기간", f"{quote['duration_months']}개월")
        st.metric("총 작업량", f"{quote['billable_workload_pm']} 인월")
        st.dataframe(
            [
                {"항목": "인건비", "금액": quote["labor_cost_krw"]},
                {"항목": "관리비", "금액": quote["management_cost_krw"]},
                {"항목": "위험버퍼", "금액": quote["risk_cost_krw"]},
                {"항목": "이익", "금액": quote["profit_margin_krw"]},
                {"항목": "최종견적", "금액": quote["final_quote_krw"]},
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            label="Markdown 견적서 다운로드",
            data=render_markdown_quote(quote, analysis),
            file_name=f"{project_name}_quote.md",
            mime="text/markdown",
        )

        html_content = f"""
        <html>
          <body>
            <h1>{project_name}</h1>
            <p>대학: {university_name}</p>
            <p>기간: {quote['duration_months']}개월</p>
            <p>최종 견적: {format_krw(quote['final_quote_krw'])}</p>
            <ul>
              {''.join(f'<li>{m}</li>' for m in quote['selected_modules'])}
            </ul>
          </body>
        </html>
        """
        st.download_button(
            label="HTML 견적서 다운로드",
            data=html_content,
            file_name=f"{project_name}_quote.html",
            mime="text/html",
        )

    with st.expander("Ontology Schema", expanded=False):
        ontology = {
            "Entities": ["University", "PIProject", "BusinessProcess", "ProjectModule", "Task", "Role", "Deliverable", "Outcome", "CostItem"],
            "Relations": ["REQUESTS", "CONTAINS", "REQUIRES", "DEPENDS_ON", "DELIVERS", "PRODUCES", "ASSIGNED_TO", "HAS_COST"],
            "Example": {
                "University": "University name and profile",
                "PIProject": "Project scope, objective, duration, complexity",
                "ProjectModule": "Selected industrial module with workload and deliverables",
            },
        }
        st.json(ontology)

    with st.expander("Knowledge Graph", expanded=False):
        graph_summary = knowledge_graph.get_graph_summary()
        st.json(graph_summary)

    with st.expander("RAG 검색 결과", expanded=False):
        st.json(analysis.get("retrieval", rag_service.retrieve(requirement_text, top_k=3)))

    with st.expander("Agent 실행 단계", expanded=False):
        st.json(analysis.get("workflow_steps", [
            "Requirement Analysis",
            "Knowledge Retrieval",
            "Workload Estimation",
            "Pricing Calculation",
            "Proposal Generation",
            "Validation",
        ]))

    with st.expander("견적 계산 근거", expanded=False):
        st.json(quote["calculation_basis"])

else:
    st.info("프로젝트 설정을 완료하고 '견적 생성' 버튼을 눌러 결과를 확인하세요.")
