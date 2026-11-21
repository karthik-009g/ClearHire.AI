from __future__ import annotations

from app.models.jobs import UserPreference
from app.services.recruiter_outreach_service import RecruiterOutreachService


def test_generate_outreach_defaults():
    service = RecruiterOutreachService()
    pkg = service.generate_outreach(company="Razorpay", role="Backend Engineer")

    assert pkg.target_company == "Razorpay"
    assert pkg.target_role == "Backend Engineer"
    assert "Razorpay" in pkg.hiring_manager_inmail
    assert "Backend Engineer" in pkg.hiring_manager_inmail
    assert len(pkg.linkedin_connection_note) <= 300
    assert "Razorpay" in pkg.linkedin_connection_note
    assert "Follow-up" in pkg.follow_up_email or "Following up" in pkg.follow_up_email
    assert len(pkg.grounded_highlights) == 3


def test_generate_outreach_with_skills_and_serving_notice():
    service = RecruiterOutreachService()
    pref = UserPreference(
        user_id=1,
        notice_period_days=15,
        serving_notice=True,
    )
    summary = {
        "skills": ["Go", "Kubernetes", "PostgreSQL", "Kafka"],
    }
    pkg = service.generate_outreach(
        company="Postman",
        role="Staff Infrastructure Engineer",
        candidate_name="Arjun",
        parsed_summary=summary,
        preferences=pref,
    )

    assert "Postman" in pkg.hiring_manager_inmail
    assert "Go" in pkg.hiring_manager_inmail
    assert "serving notice and available for early onboarding" in pkg.hiring_manager_inmail
    assert "Arjun" in pkg.hiring_manager_inmail
    assert len(pkg.linkedin_connection_note) <= 300
    assert "Postman" in pkg.linkedin_connection_note


def test_linkedin_note_strictly_under_300_chars():
    service = RecruiterOutreachService()
    pref = UserPreference(
        user_id=1,
        notice_period_days=90,
        serving_notice=False,
    )
    summary = {
        "skills": [
            "SuperLongDistributedSystemsEngineeringArchitectureSkillName1",
            "ExtremelyLongHighThroughputLowLatencyMicroservicesFrameworkSkillName2",
            "AdvancedMachineLearningNaturalLanguageProcessingModelOptimization",
        ]
    }
    pkg = service.generate_outreach(
        company="Supercalifragilisticexpialidocious Long Enterprise Holdings Limited",
        role="Senior Principal Cloud Architect and Enterprise Infrastructure Strategist",
        candidate_name="Venkatasubramanian",
        parsed_summary=summary,
        preferences=pref,
    )

    assert len(pkg.linkedin_connection_note) <= 300
