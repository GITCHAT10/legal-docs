from mnos.modules.redcoral.models import DesignBrief, StylePackage, RenderBrief, VisualApproval, DesignBaseline
from mnos.modules.buildx.models import BuildProject, WorkBreakdownStructure, Milestone
from datetime import datetime

class FenfuraaveliPilot:
    """
    FENFURAAVELI PENINSULA ESTATE
    Pilot Project 001 for RC + BX + AX Architecture.
    """
    def __init__(self, shadow, orca, fce):
        self.project_id = "RC_BX_AX_PILOT_001_FENFURAAVELI"
        self.shadow = shadow
        self.orca = orca
        self.fce = fce

    def seed_project(self):
        # 1. BUILDX Project Record
        project = BuildProject(
            project_id=self.project_id,
            title="FENFURAAVELI PENINSULA ESTATE",
            client_id="CLIENT-FENFURAAVELI",
            site_location="Fenfuraaveli, Maldives",
            status="DESIGN_IN_PROGRESS"
        )

        # 2. REDCORAL Design Brief
        brief = DesignBrief(
            project_id=self.project_id,
            client_id="CLIENT-FENFURAAVELI",
            title="Fenfuraaveli Masterplan",
            requirements=[
                "L-shaped beachfront masterplan",
                "10 plots total (Wing A: 7, Wing B: 3)",
                "Beachfront plots: 50ft x 100ft each",
                "Jungle privacy buffer",
                "3-storey spine building",
                "Hidden staff flow",
                "BOH utility backbone"
            ],
            budget_range="USD 50M - 100M"
        )

        # 3. REDCORAL Style Package
        style = StylePackage(
            package_id="STYLE-FEN-001",
            project_id=self.project_id,
            direction_name="Tropical Modern Peninsula",
            color_palette=["Sand", "Coral", "Jungle Green", "Azure"],
            materials=["Local Timber", "Coral Stone", "Thatch"],
            moodboard_urls=["https://mnos.internal/moodboard/fen-001"]
        )

        # 4. REDCORAL Render Brief
        render = RenderBrief(
            render_id="RENDER-FEN-001",
            project_id=self.project_id,
            views=["Peninsula Aerial", "Beachfront Wing A", "Spine Building Lobby"],
            resolution="8K",
            lighting_details="Sunset Warmth"
        )

        # 5. BUILDX Work Breakdown Structure
        wbs = WorkBreakdownStructure(
            wbs_id="WBS-FEN-001",
            project_id=self.project_id,
            phases=[
                {"name": "Marine Works", "description": "Peninsula stability and dredging"},
                {"name": "Civil/Structural", "description": "Spine building and plot foundations"},
                {"name": "Utility Backbone", "description": "BOH and service yard infrastructure"},
                {"name": "Guest/Staff Flows", "description": "Pathway separation and landscaping"}
            ]
        )

        # 6. BUILDX Milestones
        milestones = [
            Milestone(
                milestone_id="M1-DESIGN",
                project_id=self.project_id,
                title="Visual Approval & Baseline Locked",
                due_date=datetime(2026, 6, 1),
                payment_percentage=10.0
            ),
            Milestone(
                milestone_id="M2-MARINE",
                project_id=self.project_id,
                title="Marine Works Completion",
                due_date=datetime(2026, 9, 1),
                payment_percentage=30.0
            )
        ]

        # 7. SHADOW Seed Audit
        self.shadow.commit("demo.project.seed", "SYSTEM", {
            "project_id": self.project_id,
            "status": "INITIALIZED",
            "metadata": {
                "total_sq_ft": 50000,
                "plots": 10,
                "wing_a_plots": 7,
                "wing_b_plots": 3
            }
        })

        return {
            "project": project,
            "brief": brief,
            "style": style,
            "render": render,
            "wbs": wbs,
            "milestones": milestones
        }

    def simulate_visual_approval(self, actor_id: str):
        approval = VisualApproval(
            approval_id="APP-FEN-001",
            project_id=self.project_id,
            approver_id=actor_id,
            status="APPROVED",
            approval_hash="SHA256-FEN-APPROVED"
        )
        # Store in shadow as completion event for handoff logic
        self.shadow.commit("redcoral.design.approve.completed", actor_id, {
            "result": approval.dict(),
            "project_id": self.project_id,
            "trace_id": "T-FEN-001"
        })
        return approval

    def get_baseline(self):
        return DesignBaseline(
            project_id=self.project_id,
            version="1.0",
            specifications={
                "A_wing": "7 plots, 350 ft total",
                "B_wing": "3 plots, 150 ft total",
                "plot_size": "50x100 ft"
            },
            approved_render_hashes=["H1", "H2"],
            shadow_event_hash="S1"
        )
