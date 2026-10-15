"""Regression tests for parser problems found when a real, hand-written resume was uploaded."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.core.resume_parser import ResumeParser  # noqa: E402
from src.core.skill_ontology import extract_skills_from_text  # noqa: E402

RESUME = """ASHA RAO
Embedded and AI Engineer
Bengaluru, India | asha.rao@example.com

PROJECTS
Smart Pill Dispenser - IoT Medication System
Ongoing Capstone, 2025-Present
Manuscript in Preparation - Conference Submission
• Designing an embedded system using ESP32-S3, MQTT and RFID authentication, applying real-time control and
sensor fusion to a ward-deployable healthcare use case.
• Implementing a triple-stage verification pipeline with a load cell and servo gate control to eliminate dispensing
errors.
Line Following Robot - Autonomous Delivery
Robotics Competition, National Finalist
• Built an autonomous robot on an STM32 microcontroller with closed-loop PID control for line following.
Anomaly Detection for Motors
2025
• Optimised a Random Forest for industrial motor anomaly detection with 97 percent accuracy using Python.

TECHNICAL SKILLS
Programming: Python, Embedded-C, SQL (basics)

WORK EXPERIENCE
Production Intern
IAC Partners Automotive Pvt. Ltd. | Jan 2024 - Apr 2024
• Supported quality control and production throughput on the manufacturing floor.

EDUCATION
B.E. - Artificial Intelligence & Machine Learning | Expected: 2027

TECHNICAL ACTIVITIES & CERTIFICATIONS
• Robotics Competition, Level 2 Certificate | Hackathon 2025
Certifications: Process Automation Associate, Introduction to Automation - Example Academy (2026) | Languages: English
"""


def parse():
    return ResumeParser().parse(RESUME.encode("utf-8"), "asha_rao.txt")


def test_short_hardware_names_do_not_create_cloud_skills():
    skills = parse()["skills"]
    assert "AWS" not in skills, "ESP32-S3 must not be read as the AWS S3 service"
    assert "Terraform" not in skills, "an employer name that starts with 'IAC' must not be read as IaC"


def test_real_cloud_skills_are_still_found():
    assert "AWS" in extract_skills_from_text("Stored artefacts on AWS S3 and ran AWS Lambda functions")
    assert "Terraform" in extract_skills_from_text("Provisioned infrastructure as code with Terraform")


def test_a_four_month_internship_counts_four_months():
    exp = parse()["experience"]
    assert exp["years_of_experience"] == 0.3
    assert exp["is_fresher"] is True


def test_projects_are_whole_projects_not_wrapped_lines_or_sub_titles():
    titles = [p["title"] for p in parse()["projects"]]
    assert titles == [
        "Smart Pill Dispenser - IoT Medication System",
        "Line Following Robot - Autonomous Delivery",
        "Anomaly Detection for Motors",
    ]


def test_certifications_are_found_under_a_combined_heading_and_in_inline_lists():
    certs = parse()["certifications"]
    assert "Process Automation Associate" in certs
    assert any("Example Academy" in c for c in certs)
