"""HOD Portal sub-router."""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.hod.data import _DEPARTMENT_APPROVALS
from app.api.v1.hod.deps import get_hod_department
from app.api.v1.hod.schemas import ApprovalActionPayload, MarkCorrectionPayload
from app.core.database import get_db_session
from app.core.deps import get_current_active_user, get_tenant_context
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/curriculum", response_model=ApiResponse[dict[str, Any]])
async def get_department_curriculum(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    semester: int | None = Query(None, ge=1, le=8),
) -> ApiResponse[dict[str, Any]]:
    """Retrieve complete curriculum, subjects, allocations, CO-PO mapping, and syllabus completion."""
    dept = await get_hod_department(current_user, tenant, db)

    subjects = [
        {
            "id": "sub-cs201",
            "code": "CS201",
            "name": "Data Structures & Core Algorithms",
            "short_name": "DSA",
            "credits": 4,
            "type": "THEORY_LAB",
            "category": "CORE",
            "semester": 3,
            "regulation": "R-2026",
            "academic_year": "2026-2027",
            "assigned_faculty": "Dr. Rajesh Sharma",
            "assigned_faculty_id": "fac-001",
            "sections": ["A", "B"],
            "syllabus_completion": 85,
            "co_count": 5,
            "po_mapped": 10,
        },
        {
            "id": "sub-cs202",
            "code": "CS202",
            "name": "Object Oriented Programming in Java & C++",
            "short_name": "OOP",
            "credits": 4,
            "type": "THEORY_LAB",
            "category": "CORE",
            "semester": 3,
            "regulation": "R-2026",
            "academic_year": "2026-2027",
            "assigned_faculty": "Dr. Priya Nair",
            "assigned_faculty_id": "fac-002",
            "sections": ["A", "B"],
            "syllabus_completion": 82,
            "co_count": 5,
            "po_mapped": 8,
        },
        {
            "id": "sub-cs301",
            "code": "CS301",
            "name": "Advanced Data Structures & Analysis",
            "short_name": "ADSA",
            "credits": 4,
            "type": "THEORY_LAB",
            "category": "CORE",
            "semester": 5,
            "regulation": "R-2026",
            "academic_year": "2026-2027",
            "assigned_faculty": "Dr. Rajesh Sharma",
            "assigned_faculty_id": "fac-001",
            "sections": ["A"],
            "syllabus_completion": 80,
            "co_count": 5,
            "po_mapped": 11,
        },
        {
            "id": "sub-cs302",
            "code": "CS302",
            "name": "Database Management Systems",
            "short_name": "DBMS",
            "credits": 4,
            "type": "THEORY_LAB",
            "category": "CORE",
            "semester": 5,
            "regulation": "R-2026",
            "academic_year": "2026-2027",
            "assigned_faculty": "Dr. Priya Nair",
            "assigned_faculty_id": "fac-002",
            "sections": ["A"],
            "syllabus_completion": 86,
            "co_count": 5,
            "po_mapped": 9,
        },
        {
            "id": "sub-cs303",
            "code": "CS303",
            "name": "Computer Networks & Protocols",
            "short_name": "CN",
            "credits": 4,
            "type": "THEORY_LAB",
            "category": "CORE",
            "semester": 5,
            "regulation": "R-2026",
            "academic_year": "2026-2027",
            "assigned_faculty": "Prof. S. Ranganathan",
            "assigned_faculty_id": "fac-003",
            "sections": ["A"],
            "syllabus_completion": 74,
            "co_count": 5,
            "po_mapped": 10,
        },
        {
            "id": "sub-cs304",
            "code": "CS304",
            "name": "Design & Analysis of Algorithms",
            "short_name": "DAA",
            "credits": 3,
            "type": "THEORY",
            "category": "CORE",
            "semester": 5,
            "regulation": "R-2026",
            "academic_year": "2026-2027",
            "assigned_faculty": "Prof. K. Meenakshi",
            "assigned_faculty_id": "fac-004",
            "sections": ["A"],
            "syllabus_completion": 78,
            "co_count": 5,
            "po_mapped": 9,
        },
        {
            "id": "sub-cs401",
            "code": "CS401",
            "name": "Cloud Computing Architecture",
            "short_name": "CCA",
            "credits": 3,
            "type": "THEORY",
            "category": "ELECTIVE",
            "semester": 7,
            "regulation": "R-2026",
            "academic_year": "2026-2027",
            "assigned_faculty": "Dr. Rajesh Sharma",
            "assigned_faculty_id": "fac-001",
            "sections": ["A"],
            "syllabus_completion": 90,
            "co_count": 5,
            "po_mapped": 8,
        },
        {
            "id": "sub-cs402",
            "code": "CS402",
            "name": "Deep Learning & Neural Networks",
            "short_name": "DLNN",
            "credits": 4,
            "type": "THEORY_LAB",
            "category": "ELECTIVE",
            "semester": 7,
            "regulation": "R-2026",
            "academic_year": "2026-2027",
            "assigned_faculty": "Dr. Priya Nair",
            "assigned_faculty_id": "fac-002",
            "sections": ["A"],
            "syllabus_completion": 88,
            "co_count": 5,
            "po_mapped": 12,
        },
    ]

    if semester:
        subjects = [s for s in subjects if s["semester"] == semester]

    return ApiResponse(
        data={
            "department": dept.name,
            "regulation": "R-2026 Autonomous",
            "total_credits": 164,
            "subjects": subjects,
            "allocation_summary": {
                "total_subjects": len(subjects),
                "allocated_subjects": len(subjects),
                "unallocated_subjects": 0,
                "allocation_conflicts": 0,
            },
            "curriculum_scheme": {
                "program": "B.Tech Computer Science & Engineering",
                "academic_year": "2026-2027",
                "total_semesters": 8,
                "average_syllabus_completion": 82.8,
            },
            "course_outcomes_sample": [
                {
                    "co_code": "CO1",
                    "description": "Analyze asymptotic complexity of iterative and recursive algorithms.",
                    "bloom_level": "K4 (Analyze)",
                },
                {
                    "co_code": "CO2",
                    "description": "Design and implement self-balancing search trees and multidimensional indexes.",
                    "bloom_level": "K3 (Apply)",
                },
                {
                    "co_code": "CO3",
                    "description": "Formulate dynamic programming and greedy strategies for optimization problems.",
                    "bloom_level": "K4 (Analyze)",
                },
                {
                    "co_code": "CO4",
                    "description": "Develop graph traversal and network flow algorithms for real-world topologies.",
                    "bloom_level": "K3 (Apply)",
                },
                {
                    "co_code": "CO5",
                    "description": "Evaluate P and NP completeness concepts in computational complexity.",
                    "bloom_level": "K5 (Evaluate)",
                },
            ],
            "co_po_matrix": [
                {"co": "CO1", "PO1": 3, "PO2": 3, "PO3": 2, "PO4": 2, "PO5": 1, "PSO1": 3, "PSO2": 2},
                {"co": "CO2", "PO1": 3, "PO2": 3, "PO3": 3, "PO4": 2, "PO5": 2, "PSO1": 3, "PSO2": 2},
                {"co": "CO3", "PO1": 3, "PO2": 2, "PO3": 3, "PO4": 3, "PO5": 2, "PSO1": 3, "PSO2": 3},
                {"co": "CO4", "PO1": 2, "PO2": 3, "PO3": 2, "PO4": 2, "PO5": 2, "PSO1": 2, "PSO2": 3},
                {"co": "CO5", "PO1": 3, "PO2": 2, "PO3": 1, "PO4": 1, "PO5": 1, "PSO1": 2, "PSO2": 1},
            ],
        }
    )


@router.get("/lesson-plans", response_model=ApiResponse[dict[str, Any]])
async def get_department_lesson_plans(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    subject_code: str | None = Query(None),
) -> ApiResponse[dict[str, Any]]:
    """Retrieve faculty lesson plan progress, planned vs completed topics, and syllabus completion."""
    dept = await get_hod_department(current_user, tenant, db)

    plans = [
        {
            "id": "lp-cs301",
            "course_code": "CS301",
            "course_name": "Advanced Data Structures & Analysis",
            "section": "A",
            "faculty_name": "Dr. Rajesh Sharma",
            "faculty_designation": "Professor & Dean",
            "total_planned_hours": 45,
            "total_completed_hours": 36,
            "overall_completion_percentage": 80.0,
            "status": "IN_PROGRESS",
            "pending_plans_count": 0,
            "units": [
                {
                    "unit_number": 1,
                    "title": "Linear Data Structures & Complexity Analysis",
                    "planned_hours": 9,
                    "completed_hours": 9,
                    "status": "COMPLETED",
                    "completion_percentage": 100,
                    "topics": [
                        {"topic": "Asymptotic notations & Big-O complexity", "completed": True},
                        {"topic": "Amortized complexity of dynamic tables", "completed": True},
                        {"topic": "Singly and doubly linked lists operations", "completed": True},
                        {"topic": "Stack and queue memory abstractions", "completed": True},
                    ],
                },
                {
                    "unit_number": 2,
                    "title": "Hierarchical Structures & Balanced Trees",
                    "planned_hours": 10,
                    "completed_hours": 10,
                    "status": "COMPLETED",
                    "completion_percentage": 100,
                    "topics": [
                        {"topic": "Binary search trees insertion and deletion", "completed": True},
                        {"topic": "AVL Tree single and double rotations", "completed": True},
                        {"topic": "Red-Black Tree coloring invariants", "completed": True},
                        {"topic": "B-Trees and B+ Trees for secondary storage indexing", "completed": True},
                    ],
                },
                {
                    "unit_number": 3,
                    "title": "Heaps & Disjoint Set Forests",
                    "planned_hours": 8,
                    "completed_hours": 8,
                    "status": "COMPLETED",
                    "completion_percentage": 100,
                    "topics": [
                        {"topic": "Min/Max Binary Heaps and Heapify", "completed": True},
                        {"topic": "Binomial Heaps and merge operations", "completed": True},
                        {"topic": "Fibonacci Heaps and amortized extract-min", "completed": True},
                        {"topic": "Disjoint set union by rank and path compression", "completed": True},
                    ],
                },
                {
                    "unit_number": 4,
                    "title": "Graph Algorithms & Shortest Paths",
                    "planned_hours": 10,
                    "completed_hours": 7,
                    "status": "IN_PROGRESS",
                    "completion_percentage": 70,
                    "topics": [
                        {"topic": "Breadth-first and depth-first traversals", "completed": True},
                        {"topic": "Dijkstra algorithm with priority queues", "completed": True},
                        {"topic": "Bellman-Ford and negative cycle detection", "completed": True},
                        {"topic": "All-pairs shortest paths: Floyd-Warshall", "completed": False},
                        {"topic": "Network maximum flow: Ford-Fulkerson", "completed": False},
                    ],
                },
                {
                    "unit_number": 5,
                    "title": "NP-Completeness & Approximation Algorithms",
                    "planned_hours": 8,
                    "completed_hours": 2,
                    "status": "IN_PROGRESS",
                    "completion_percentage": 25,
                    "topics": [
                        {"topic": "Polynomial time reductions and Turing reductions", "completed": True},
                        {"topic": "Classes P, NP, NP-Hard, and NP-Complete", "completed": False},
                        {"topic": "Cook-Levin theorem overview", "completed": False},
                        {"topic": "Vertex cover and Traveling Salesperson approximations", "completed": False},
                    ],
                },
            ],
        },
        {
            "id": "lp-cs302",
            "course_code": "CS302",
            "course_name": "Database Management Systems",
            "section": "A",
            "faculty_name": "Dr. Priya Nair",
            "faculty_designation": "Associate Professor",
            "total_planned_hours": 45,
            "total_completed_hours": 39,
            "overall_completion_percentage": 86.6,
            "status": "IN_PROGRESS",
            "pending_plans_count": 0,
            "units": [
                {
                    "unit_number": 1,
                    "title": "Relational Data Model & SQL Queries",
                    "planned_hours": 9,
                    "completed_hours": 9,
                    "status": "COMPLETED",
                    "completion_percentage": 100,
                    "topics": [
                        {"topic": "ER Modeling and relational schema translation", "completed": True},
                        {"topic": "Relational algebra operations", "completed": True},
                        {"topic": "Complex SQL joins and aggregate groupings", "completed": True},
                    ],
                },
                {
                    "unit_number": 2,
                    "title": "Normalization & Functional Dependencies",
                    "planned_hours": 9,
                    "completed_hours": 9,
                    "status": "COMPLETED",
                    "completion_percentage": 100,
                    "topics": [
                        {"topic": "1NF, 2NF, 3NF, BCNF decomposition", "completed": True},
                        {"topic": "Lossless join and dependency preservation", "completed": True},
                    ],
                },
                {
                    "unit_number": 3,
                    "title": "Transaction Processing & Concurrency Control",
                    "planned_hours": 10,
                    "completed_hours": 10,
                    "status": "COMPLETED",
                    "completion_percentage": 100,
                    "topics": [
                        {"topic": "ACID properties and serializability schedules", "completed": True},
                        {"topic": "Two-phase locking protocol (2PL)", "completed": True},
                        {"topic": "Timestamp-based ordering protocols", "completed": True},
                    ],
                },
                {
                    "unit_number": 4,
                    "title": "Query Processing & Optimization",
                    "planned_hours": 9,
                    "completed_hours": 8,
                    "status": "IN_PROGRESS",
                    "completion_percentage": 88,
                    "topics": [
                        {"topic": "Query tree generation and heuristic optimization", "completed": True},
                        {"topic": "Cost-based execution plan estimation", "completed": True},
                    ],
                },
                {
                    "unit_number": 5,
                    "title": "Distributed Databases & NoSQL Storage",
                    "planned_hours": 8,
                    "completed_hours": 3,
                    "status": "IN_PROGRESS",
                    "completion_percentage": 37,
                    "topics": [
                        {"topic": "CAP Theorem and BASE architecture", "completed": True},
                        {"topic": "Document-oriented databases (MongoDB)", "completed": False},
                        {"topic": "Columnar stores and distributed sharding", "completed": False},
                    ],
                },
            ],
        },
        {
            "id": "lp-cs303",
            "course_code": "CS303",
            "course_name": "Computer Networks & Protocols",
            "section": "A",
            "faculty_name": "Prof. S. Ranganathan",
            "faculty_designation": "Assistant Professor",
            "total_planned_hours": 45,
            "total_completed_hours": 33,
            "overall_completion_percentage": 73.3,
            "status": "IN_PROGRESS",
            "pending_plans_count": 1,
            "units": [
                {
                    "unit_number": 1,
                    "title": "Physical Layer & Media Access Control",
                    "planned_hours": 9,
                    "completed_hours": 9,
                    "status": "COMPLETED",
                    "completion_percentage": 100,
                    "topics": [
                        {"topic": "OSI and TCP/IP protocol layering", "completed": True},
                        {"topic": "Ethernet 802.3 and CSMA/CD protocols", "completed": True},
                    ],
                },
                {
                    "unit_number": 2,
                    "title": "Network Layer & IPv4/IPv6 Routing",
                    "planned_hours": 10,
                    "completed_hours": 10,
                    "status": "COMPLETED",
                    "completion_percentage": 100,
                    "topics": [
                        {"topic": "CIDR subnetting and supernetting", "completed": True},
                        {"topic": "OSPF Link-State and BGP Path-Vector", "completed": True},
                    ],
                },
                {
                    "unit_number": 3,
                    "title": "Transport Layer & Congestion Control",
                    "planned_hours": 9,
                    "completed_hours": 8,
                    "status": "IN_PROGRESS",
                    "completion_percentage": 88,
                    "topics": [
                        {"topic": "TCP three-way handshake and connection teardown", "completed": True},
                        {"topic": "TCP Reno and Cubic congestion window scaling", "completed": True},
                    ],
                },
                {
                    "unit_number": 4,
                    "title": "Application Layer & Network Security",
                    "planned_hours": 9,
                    "completed_hours": 5,
                    "status": "IN_PROGRESS",
                    "completion_percentage": 55,
                    "topics": [
                        {"topic": "DNS hierarchy and iterative resolution", "completed": True},
                        {"topic": "TLS 1.3 cryptographic handshakes", "completed": False},
                    ],
                },
                {
                    "unit_number": 5,
                    "title": "Software Defined Networking (SDN)",
                    "planned_hours": 8,
                    "completed_hours": 1,
                    "status": "IN_PROGRESS",
                    "completion_percentage": 12,
                    "topics": [
                        {"topic": "Separation of control and data planes", "completed": True},
                        {"topic": "OpenFlow protocol and centralized controllers", "completed": False},
                    ],
                },
            ],
        },
    ]

    if subject_code:
        plans = [p for p in plans if p["course_code"].upper() == subject_code.upper()]

    return ApiResponse(
        data={
            "department": dept.name,
            "lesson_plans": plans,
            "summary": {
                "total_monitored_courses": len(plans),
                "average_syllabus_completion": round(
                    sum(p["overall_completion_percentage"] for p in plans) / len(plans), 1
                ),
                "courses_behind_schedule": sum(
                    1 for p in plans if p["overall_completion_percentage"] < 75.0
                ),
                "pending_lesson_plans": sum(p["pending_plans_count"] for p in plans),
            },
        }
    )


@router.get("/examinations", response_model=ApiResponse[dict[str, Any]])
async def get_department_examinations(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, Any]]:
    """Retrieve examination schedules, terms, marks submission progress, and missing marks radar."""
    dept = await get_hod_department(current_user, tenant, db)

    terms = [
        {
            "id": "term-ia1",
            "name": "Internal Assessment Test 1 (IA-1)",
            "academic_year": "2026-2027",
            "status": "COMPLETED",
            "start_date": "2026-09-15",
            "end_date": "2026-09-22",
            "marks_submission_deadline": "2026-09-28",
            "submission_status": "COMPLETED (100%)",
        },
        {
            "id": "term-ia2",
            "name": "Internal Assessment Test 2 (IA-2)",
            "academic_year": "2026-2027",
            "status": "COMPLETED",
            "start_date": "2026-10-20",
            "end_date": "2026-10-27",
            "marks_submission_deadline": "2026-11-04",
            "submission_status": "PENDING_VERIFICATION (92%)",
        },
        {
            "id": "term-model",
            "name": "Model Examination Nov 2026",
            "academic_year": "2026-2027",
            "status": "ONGOING",
            "start_date": "2026-11-18",
            "end_date": "2026-11-26",
            "marks_submission_deadline": "2026-12-02",
            "submission_status": "IN_PROGRESS",
        },
        {
            "id": "term-ese",
            "name": "End Semester Autonomous Theory Examinations",
            "academic_year": "2026-2027",
            "status": "UPCOMING",
            "start_date": "2026-12-08",
            "end_date": "2026-12-22",
            "marks_submission_deadline": "2027-01-05",
            "submission_status": "SCHEDULED",
        },
    ]

    schedules = [
        {
            "id": "sch-001",
            "date": "2026-11-18",
            "time": "10:00 AM - 01:00 PM",
            "duration": "3 Hours",
            "course_code": "CS301",
            "course_name": "Advanced Data Structures & Analysis",
            "semester": 5,
            "section": "A",
            "exam_type": "MODEL_EXAMINATION",
            "hall_number": "EXAM-HALL-301",
            "chief_invigilator": "Dr. Rajesh Sharma",
            "total_candidates": 68,
        },
        {
            "id": "sch-002",
            "date": "2026-11-20",
            "time": "10:00 AM - 01:00 PM",
            "duration": "3 Hours",
            "course_code": "CS302",
            "course_name": "Database Management Systems",
            "semester": 5,
            "section": "A",
            "exam_type": "MODEL_EXAMINATION",
            "hall_number": "EXAM-HALL-302",
            "chief_invigilator": "Dr. Priya Nair",
            "total_candidates": 68,
        },
        {
            "id": "sch-003",
            "date": "2026-11-22",
            "time": "10:00 AM - 01:00 PM",
            "duration": "3 Hours",
            "course_code": "CS303",
            "course_name": "Computer Networks & Protocols",
            "semester": 5,
            "section": "A",
            "exam_type": "MODEL_EXAMINATION",
            "hall_number": "EXAM-HALL-303",
            "chief_invigilator": "Prof. S. Ranganathan",
            "total_candidates": 68,
        },
        {
            "id": "sch-004",
            "date": "2026-11-24",
            "time": "10:00 AM - 01:00 PM",
            "duration": "3 Hours",
            "course_code": "CS304",
            "course_name": "Design & Analysis of Algorithms",
            "semester": 5,
            "section": "A",
            "exam_type": "MODEL_EXAMINATION",
            "hall_number": "EXAM-HALL-304",
            "chief_invigilator": "Prof. K. Meenakshi",
            "total_candidates": 68,
        },
    ]

    submission_progress = [
        {
            "course_code": "CS301",
            "course_name": "Advanced Data Structures & Analysis",
            "faculty_name": "Dr. Rajesh Sharma",
            "ia1_status": "SUBMITTED",
            "ia2_status": "SUBMITTED",
            "model_status": "PENDING_EVALUATION",
            "pending_count": 0,
            "missing_marks": 0,
        },
        {
            "course_code": "CS302",
            "course_name": "Database Management Systems",
            "faculty_name": "Dr. Priya Nair",
            "ia1_status": "SUBMITTED",
            "ia2_status": "SUBMITTED",
            "model_status": "PENDING_EVALUATION",
            "pending_count": 0,
            "missing_marks": 0,
        },
        {
            "course_code": "CS303",
            "course_name": "Computer Networks & Protocols",
            "faculty_name": "Prof. S. Ranganathan",
            "ia1_status": "SUBMITTED",
            "ia2_status": "PARTIAL (64/68)",
            "model_status": "NOT_STARTED",
            "pending_count": 4,
            "missing_marks": 4,
        },
    ]

    return ApiResponse(
        data={
            "department": dept.name,
            "terms": terms,
            "schedules": schedules,
            "submission_progress": submission_progress,
            "summary": {
                "total_scheduled_exams": len(schedules),
                "ongoing_exams": 1,
                "completed_terms": 2,
                "missing_marks_total": 4,
                "submission_compliance_rate": 95.6,
            },
        }
    )


@router.get("/internal-marks", response_model=ApiResponse[dict[str, Any]])
async def get_department_internal_marks(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    semester: int | None = Query(None, ge=1, le=8),
    course_code: str | None = Query(None),
) -> ApiResponse[dict[str, Any]]:
    """Retrieve department internal assessment ledger, component breakdown, and shortage radar."""
    dept = await get_hod_department(current_user, tenant, db)

    records = [
        {
            "id": "im-001",
            "student_id": "std-001",
            "student_name": "Aarav Patel",
            "roll_number": "24CSE0101",
            "semester": 5,
            "section": "A",
            "course_code": "CS301",
            "course_name": "Advanced Data Structures & Analysis",
            "faculty_name": "Dr. Rajesh Sharma",
            "ia1": 24,  # max 25
            "ia2": 23,  # max 25
            "ia3_model": 46,  # max 50
            "assignments": 19,  # max 20
            "attendance_score": 10,  # max 10
            "total_internal": 47.5,  # scaled to 50
            "max_internal": 50.0,
            "percentage": 95.0,
            "status": "FINALIZED",
            "requires_attention": False,
        },
        {
            "id": "im-002",
            "student_id": "std-002",
            "student_name": "Diya Sharma",
            "roll_number": "24CSE0102",
            "semester": 5,
            "section": "A",
            "course_code": "CS301",
            "course_name": "Advanced Data Structures & Analysis",
            "faculty_name": "Dr. Rajesh Sharma",
            "ia1": 22,
            "ia2": 21,
            "ia3_model": 43,
            "assignments": 18,
            "attendance_score": 8,
            "total_internal": 44.0,
            "max_internal": 50.0,
            "percentage": 88.0,
            "status": "FINALIZED",
            "requires_attention": False,
        },
        {
            "id": "im-003",
            "student_id": "std-003",
            "student_name": "Rohan Iyer",
            "roll_number": "24CSE0103",
            "semester": 5,
            "section": "A",
            "course_code": "CS301",
            "course_name": "Advanced Data Structures & Analysis",
            "faculty_name": "Dr. Rajesh Sharma",
            "ia1": 15,
            "ia2": 14,
            "ia3_model": 28,
            "assignments": 12,
            "attendance_score": 6,
            "total_internal": 29.5,
            "max_internal": 50.0,
            "percentage": 59.0,
            "status": "VERIFIED",
            "requires_attention": False,
        },
        {
            "id": "im-004",
            "student_id": "std-004",
            "student_name": "Ananya Reddy",
            "roll_number": "24CSE0104",
            "semester": 5,
            "section": "A",
            "course_code": "CS301",
            "course_name": "Advanced Data Structures & Analysis",
            "faculty_name": "Dr. Rajesh Sharma",
            "ia1": 24,
            "ia2": 24,
            "ia3_model": 48,
            "assignments": 19,
            "attendance_score": 9,
            "total_internal": 48.0,
            "max_internal": 50.0,
            "percentage": 96.0,
            "status": "FINALIZED",
            "requires_attention": False,
        },
        {
            "id": "im-005",
            "student_id": "std-005",
            "student_name": "Karthik Raja",
            "roll_number": "24CSE0105",
            "semester": 5,
            "section": "A",
            "course_code": "CS303",
            "course_name": "Computer Networks & Protocols",
            "faculty_name": "Prof. S. Ranganathan",
            "ia1": 11,
            "ia2": 10,
            "ia3_model": 20,
            "assignments": 10,
            "attendance_score": 5,
            "total_internal": 21.0,
            "max_internal": 50.0,
            "percentage": 42.0,
            "status": "ENTERED",
            "requires_attention": True,
        },
    ]

    if semester:
        records = [r for r in records if r["semester"] == semester]
    if course_code:
        records = [r for r in records if r["course_code"].upper() == course_code.upper()]

    attention_list = [r for r in records if r["requires_attention"] or r["percentage"] < 50.0]

    return ApiResponse(
        data={
            "department": dept.name,
            "records": records,
            "attention_list": attention_list,
            "summary": {
                "total_records": len(records),
                "average_percentage": round(sum(r["percentage"] for r in records) / len(records), 1)
                if records
                else 0.0,
                "students_requiring_attention": len(attention_list),
                "missing_marks_count": 1,
            },
        }
    )


@router.post("/internal-marks/correction-request", response_model=ApiResponse[dict[str, Any]])
async def request_internal_marks_correction(
    payload: MarkCorrectionPayload,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, Any]]:
    """Submit a formal marks correction request with audit history for HOD verification."""
    dept = await get_hod_department(current_user, tenant, db)

    now_iso = datetime.now(UTC).isoformat()
    record = {
        "correction_id": f"corr-{int(datetime.now().timestamp())}",
        "department": dept.name,
        "student_id": payload.student_id,
        "assessment_id": payload.assessment_id,
        "course_code": payload.course_code,
        "original_mark": payload.original_mark,
        "requested_mark": payload.requested_mark,
        "reason": payload.reason,
        "status": "PENDING_AUDIT",
        "submitted_by": current_user.full_name or "HOD User",
        "created_at": now_iso,
        "audit_trail": [
            {
                "action": "CORRECTION_REQUESTED",
                "by": current_user.full_name or "HOD User",
                "timestamp": now_iso,
                "notes": payload.reason,
            }
        ],
    }

    return ApiResponse(data=record)


@router.get("/results", response_model=ApiResponse[dict[str, Any]])
async def get_department_semester_results(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    semester: int | None = Query(None, ge=1, le=8),
) -> ApiResponse[dict[str, Any]]:
    """Retrieve comprehensive semester results, pass percentage, toppers, and arrear analytics."""
    dept = await get_hod_department(current_user, tenant, db)

    overview = {
        "academic_year": "2026-2027",
        "examination": "Autonomous End Semester Examinations (Previous Academic Term)",
        "total_students_appeared": 240,
        "total_students_passed": 218,
        "total_students_failed": 22,
        "pass_percentage": 90.8,
        "previous_semester_pass_percentage": 88.5,
        "percentage_delta": "+2.3%",
    }

    subject_results = [
        {
            "course_code": "CS301",
            "course_name": "Advanced Data Structures & Analysis",
            "faculty": "Dr. Rajesh Sharma",
            "appeared": 68,
            "passed": 64,
            "failed": 4,
            "pass_percentage": 94.1,
            "average_grade_point": 8.3,
        },
        {
            "course_code": "CS302",
            "course_name": "Database Management Systems",
            "faculty": "Dr. Priya Nair",
            "appeared": 68,
            "passed": 63,
            "failed": 5,
            "pass_percentage": 92.6,
            "average_grade_point": 8.1,
        },
        {
            "course_code": "CS303",
            "course_name": "Computer Networks & Protocols",
            "faculty": "Prof. S. Ranganathan",
            "appeared": 68,
            "passed": 58,
            "failed": 10,
            "pass_percentage": 85.3,
            "average_grade_point": 7.4,
        },
        {
            "course_code": "CS304",
            "course_name": "Design & Analysis of Algorithms",
            "faculty": "Prof. K. Meenakshi",
            "appeared": 68,
            "passed": 61,
            "failed": 7,
            "pass_percentage": 89.7,
            "average_grade_point": 7.8,
        },
    ]

    toppers = [
        {
            "rank": 1,
            "roll_number": "24CSE0101",
            "name": "Aarav Patel",
            "semester": 5,
            "cgpa": 9.42,
            "sgpa": 9.60,
            "total_credits": 104,
            "arrears": 0,
            "status": "FIRST_CLASS_DISTINCTION",
        },
        {
            "rank": 2,
            "roll_number": "24CSE0104",
            "name": "Ananya Reddy",
            "semester": 5,
            "cgpa": 9.15,
            "sgpa": 9.30,
            "total_credits": 104,
            "arrears": 0,
            "status": "FIRST_CLASS_DISTINCTION",
        },
        {
            "rank": 3,
            "roll_number": "24CSE0102",
            "name": "Diya Sharma",
            "semester": 5,
            "cgpa": 8.84,
            "sgpa": 8.90,
            "total_credits": 104,
            "arrears": 0,
            "status": "FIRST_CLASS_DISTINCTION",
        },
    ]

    support_list = [
        {
            "roll_number": "24CSE0103",
            "name": "Rohan Iyer",
            "semester": 5,
            "cgpa": 6.12,
            "sgpa": 5.80,
            "arrears": 1,
            "arrear_subjects": ["CS303 Computer Networks"],
            "support_plan": "Peer tutoring and Saturday remedial coaching scheduled.",
        },
        {
            "roll_number": "24CSE0105",
            "name": "Karthik Raja",
            "semester": 5,
            "cgpa": 5.94,
            "sgpa": 5.50,
            "arrears": 2,
            "arrear_subjects": ["CS303 Computer Networks", "CS304 DAA"],
            "support_plan": "Parent-Teacher meeting scheduled; faculty mentor assigned.",
        },
    ]

    arrear_analytics = {
        "total_students_with_arrears": 22,
        "single_arrear_count": 16,
        "multiple_arrears_count": 6,
        "repeated_arrears_count": 3,
        "subject_wise_arrear_breakdown": [
            {"course_code": "CS303", "subject": "Computer Networks", "arrear_count": 10},
            {"course_code": "CS304", "subject": "Design & Analysis of Algorithms", "arrear_count": 7},
            {"course_code": "CS302", "subject": "Database Systems", "arrear_count": 5},
            {"course_code": "CS301", "subject": "Advanced Data Structures", "arrear_count": 4},
        ],
    }

    return ApiResponse(
        data={
            "department": dept.name,
            "overview": overview,
            "subject_results": subject_results,
            "toppers": toppers,
            "students_needing_support": support_list,
            "arrear_analytics": arrear_analytics,
        }
    )


@router.get("/approvals", response_model=ApiResponse[dict[str, Any]])
async def get_department_approvals(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    category: str = Query("ALL", description="ALL, FACULTY, STUDENT, or DEPARTMENT"),
    status_filter: str = Query("ALL", description="ALL, PENDING, APPROVED, REJECTED, INFO_REQUESTED"),
) -> ApiResponse[dict[str, Any]]:
    """Retrieve central departmental statutory approvals queue for HOD review."""
    dept = await get_hod_department(current_user, tenant, db)

    items = _DEPARTMENT_APPROVALS
    if category != "ALL":
        items = [i for i in items if i["category"].upper() == category.upper()]
    if status_filter != "ALL":
        items = [i for i in items if i["status"].upper() == status_filter.upper()]

    stats = {
        "total_requests": len(_DEPARTMENT_APPROVALS),
        "pending": sum(1 for i in _DEPARTMENT_APPROVALS if i["status"] == "PENDING"),
        "approved": sum(1 for i in _DEPARTMENT_APPROVALS if i["status"] == "APPROVED"),
        "rejected": sum(1 for i in _DEPARTMENT_APPROVALS if i["status"] == "REJECTED"),
        "info_requested": sum(1 for i in _DEPARTMENT_APPROVALS if i["status"] == "INFO_REQUESTED"),
    }

    return ApiResponse(
        data={
            "department": dept.name,
            "stats": stats,
            "requests": items,
        }
    )


@router.post("/approvals/{approval_id}/action", response_model=ApiResponse[dict[str, Any]])
async def process_department_approval_action(
    approval_id: str,
    payload: ApprovalActionPayload,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, Any]]:
    """Execute HOD approval decision (APPROVE, REJECT, or REQUEST_INFO) with full audit logging."""
    dept = await get_hod_department(current_user, tenant, db)

    valid_actions = {"APPROVE", "REJECT", "REQUEST_INFO"}
    if payload.action not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid approval action '{payload.action}'. Must be one of {valid_actions}.",
        )

    target = next((a for a in _DEPARTMENT_APPROVALS if a["id"] == approval_id), None)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval request with ID '{approval_id}' was not found.",
        )

    # Department RBAC check
    if target["department_id"] != dept.code.lower() and dept.name not in target["department_name"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: HOD can only act upon approval requests within their assigned department.",
        )

    now_iso = datetime.now(UTC).isoformat()
    status_map = {
        "APPROVE": "APPROVED",
        "REJECT": "REJECTED",
        "REQUEST_INFO": "INFO_REQUESTED",
    }
    new_status = status_map[payload.action]

    target["status"] = new_status
    target["remarks"] = payload.remarks
    target["decided_by"] = current_user.full_name or "Dr. K. S. Anand (HOD)"
    target["decision_date"] = now_iso

    audit_entry = {
        "action": new_status,
        "by": current_user.full_name or "Dr. K. S. Anand (HOD)",
        "timestamp": now_iso,
        "notes": payload.remarks or f"Decision {new_status} rendered by HOD.",
    }
    target["audit_trail"].append(audit_entry)

    return ApiResponse(data=target)

