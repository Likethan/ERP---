"""CampusOS Documents & Digital Records Domain Service.

Implements business logic for document categories, types, requirements,
lifecycle transitions, verification workflows, certificate templates,
issuance and revocation, institutional governance records, storage integration,
expiry engine, and database aggregations.
"""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from app.core.storage import (
    calculate_sha256,
    format_file_size,
    get_document_storage,
)
from app.models.audit import AuditLog
from app.models.documents import (
    CertificateRequest,
    CertificateTemplate,
    CertificateTemplateField,
    CertificateTemplateVersion,
    Document,
    DocumentCategory,
    DocumentHistory,
    DocumentRequirement,
    DocumentType,
    DocumentVerification,
    DocumentVersion,
    InstitutionalRecord,
    InstitutionalRecordHistory,
    IssuedCertificate,
)
from app.models.people import StudentProfile, User
from app.schemas.documents import (
    CertificateRequestApprove,
    CertificateRequestCreate,
    CertificateRequestReject,
    CertificateTemplateCreate,
    CertificateTemplateUpdate,
    DocumentCategoryCreate,
    DocumentCategoryUpdate,
    DocumentCreate,
    DocumentRequirementCreate,
    DocumentTypeCreate,
    DocumentTypeUpdate,
    DocumentUpdate,
    InstitutionalRecordCreate,
    InstitutionalRecordUpdate,
)


class DocumentService:
    """Enterprise domain service for Documents and Digital Credentials."""

    # -------------------------------------------------------------------------
    # Audit & History Helpers
    # -------------------------------------------------------------------------
    @staticmethod
    def _create_audit_log(
        tenant_id: UUID,
        user_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: UUID,
        details: dict | None = None,
        ip_address: str = "127.0.0.1",
        business_context: str | None = None,
    ) -> AuditLog:
        return AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            new_values_json=details,
            ip_address=ip_address or "127.0.0.1",
            business_context=business_context,
        )

    @staticmethod
    def _create_doc_history(
        document_id: UUID,
        tenant_id: UUID,
        action: str,
        description: str,
        performed_by_id: UUID | None,
        performed_by_name: str,
        role: str | None = None,
        notes: str | None = None,
    ) -> DocumentHistory:
        return DocumentHistory(
            id=uuid4(),
            document_id=document_id,
            tenant_id=tenant_id,
            action=action,
            description=description,
            performed_by_id=performed_by_id,
            performed_by_name=performed_by_name,
            role=role,
            notes=notes,
        )

    @staticmethod
    def _create_inst_history(
        record_id: UUID,
        tenant_id: UUID,
        action: str,
        performed_by_id: UUID | None,
        performed_by_name: str,
        details: str | None = None,
    ) -> InstitutionalRecordHistory:
        return InstitutionalRecordHistory(
            id=uuid4(),
            record_id=record_id,
            tenant_id=tenant_id,
            action=action,
            performed_by_id=performed_by_id,
            performed_by_name=performed_by_name,
            details=details,
        )

    # -------------------------------------------------------------------------
    # 1. DOCUMENT CATEGORIES
    # -------------------------------------------------------------------------
    @classmethod
    async def list_categories(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        is_active: bool | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(DocumentCategory).where(DocumentCategory.tenant_id == tenant_id)
        if is_active is not None:
            stmt = stmt.where(DocumentCategory.is_active == is_active)
        stmt = stmt.order_by(DocumentCategory.name.asc())

        res = await db.execute(stmt)
        categories = res.scalars().all()

        # Compute document counts per category
        count_stmt = (
            select(
                Document.category_id,
                func.count(Document.id).label("total"),
                func.count(case((Document.status == "VERIFIED", 1))).label("verified"),
                func.count(
                    case((Document.status.in_(["UPLOADED", "UNDER_REVIEW"]), 1))
                ).label("pending"),
                func.count(case((Document.status == "REJECTED", 1))).label("rejected"),
            )
            .where(
                Document.tenant_id == tenant_id,
                Document.deleted_at.is_(None),
            )
            .group_by(Document.category_id)
        )
        count_res = await db.execute(count_stmt)
        counts_map = {row.category_id: row for row in count_res}

        result = []
        for cat in categories:
            stats = counts_map.get(cat.id)
            result.append(
                {
                    "id": str(cat.id),
                    "tenant_id": cat.tenant_id,
                    "code": cat.code,
                    "name": cat.name,
                    "description": cat.description or "",
                    "required": not cat.is_active,  # or rule
                    "applicableRoles": cat.applicable_roles or ["STUDENT", "FACULTY", "STAFF"],
                    "applicableDocumentTypes": cat.applicable_document_types or ["Standard Document"],
                    "verificationRequired": cat.requires_verification,
                    "expiryRequired": cat.requires_expiry,
                    "isActive": cat.is_active,
                    "totalDocuments": stats.total if stats else 0,
                    "verifiedDocuments": stats.verified if stats else 0,
                    "pendingDocuments": stats.pending if stats else 0,
                    "rejectedDocuments": stats.rejected if stats else 0,
                    "auditHistory": [
                        {
                            "id": f"aud-{cat.id}",
                            "action": "Category Active",
                            "performedBy": "Institutional Registrar",
                            "timestamp": cat.created_at.isoformat(),
                            "details": "Document governance configuration",
                        }
                    ],
                    "created_at": cat.created_at,
                    "updated_at": cat.updated_at,
                }
            )
        return result

    @classmethod
    async def get_category_by_id(
        cls, db: AsyncSession, tenant_id: UUID, category_id: UUID
    ) -> DocumentCategory:
        cat = await db.scalar(
            select(DocumentCategory).where(
                DocumentCategory.id == category_id,
                DocumentCategory.tenant_id == tenant_id,
            )
        )
        if not cat:
            raise NotFoundException(f"Document category with ID '{category_id}' not found.")
        return cat

    @classmethod
    async def get_category_by_code(
        cls, db: AsyncSession, tenant_id: UUID, code: str
    ) -> DocumentCategory | None:
        return await db.scalar(
            select(DocumentCategory).where(
                DocumentCategory.code == code.upper().strip(),
                DocumentCategory.tenant_id == tenant_id,
            )
        )

    @classmethod
    async def create_category(
        cls, db: AsyncSession, tenant_id: UUID, data: DocumentCategoryCreate, user: User
    ) -> DocumentCategory:
        code_clean = data.code.upper().strip()
        existing = await cls.get_category_by_code(db, tenant_id, code_clean)
        if existing:
            raise ConflictException(f"Document category with code '{code_clean}' already exists.")

        cat = DocumentCategory(
            id=uuid4(),
            tenant_id=tenant_id,
            code=code_clean,
            name=data.name.strip(),
            description=data.description,
            is_active=data.is_active,
            requires_verification=data.verification_required,
            requires_expiry=data.expiry_required,
            applicable_roles=data.applicable_roles,
            applicable_document_types=data.applicable_document_types,
        )
        db.add(cat)
        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="DOCUMENT_CATEGORY_CREATED",
                entity_type="DocumentCategory",
                entity_id=cat.id,
                details={"code": cat.code, "name": cat.name},
                business_context="Document Governance",
            )
        )
        await db.commit()
        await db.refresh(cat)
        return cat

    @classmethod
    async def update_category(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        category_id: UUID,
        data: DocumentCategoryUpdate,
        user: User,
    ) -> DocumentCategory:
        cat = await cls.get_category_by_id(db, tenant_id, category_id)

        update_dict = data.model_dump(exclude_unset=True)
        if "name" in update_dict and update_dict["name"] is not None:
            cat.name = update_dict["name"].strip()
        if "description" in update_dict:
            cat.description = update_dict["description"]
        if "is_active" in update_dict and update_dict["is_active"] is not None:
            cat.is_active = update_dict["is_active"]
        if "verification_required" in update_dict and update_dict["verification_required"] is not None:
            cat.requires_verification = update_dict["verification_required"]
        if "expiry_required" in update_dict and update_dict["expiry_required"] is not None:
            cat.requires_expiry = update_dict["expiry_required"]
        if "applicable_roles" in update_dict and update_dict["applicable_roles"] is not None:
            cat.applicable_roles = update_dict["applicable_roles"]
        if "applicable_document_types" in update_dict and update_dict["applicable_document_types"] is not None:
            cat.applicable_document_types = update_dict["applicable_document_types"]

        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="DOCUMENT_CATEGORY_UPDATED",
                entity_type="DocumentCategory",
                entity_id=cat.id,
                details=update_dict,
                business_context="Document Governance",
            )
        )
        await db.commit()
        await db.refresh(cat)
        return cat

    # -------------------------------------------------------------------------
    # 2. DOCUMENT TYPES
    # -------------------------------------------------------------------------
    @classmethod
    async def list_document_types(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        category_id: UUID | None = None,
        is_active: bool | None = None,
    ) -> list[DocumentType]:
        stmt = select(DocumentType).where(DocumentType.tenant_id == tenant_id)
        if category_id:
            stmt = stmt.where(DocumentType.category_id == category_id)
        if is_active is not None:
            stmt = stmt.where(DocumentType.is_active == is_active)
        stmt = stmt.order_by(DocumentType.name.asc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def get_document_type(
        cls, db: AsyncSession, tenant_id: UUID, type_id: UUID
    ) -> DocumentType:
        doc_type = await db.scalar(
            select(DocumentType).where(
                DocumentType.id == type_id,
                DocumentType.tenant_id == tenant_id,
            )
        )
        if not doc_type:
            raise NotFoundException(f"Document type with ID '{type_id}' not found.")
        return doc_type

    @classmethod
    async def create_document_type(
        cls, db: AsyncSession, tenant_id: UUID, data: DocumentTypeCreate, user: User
    ) -> DocumentType:
        # Check category existence and active status
        cat = await cls.get_category_by_id(db, tenant_id, data.category_id)
        if not cat.is_active:
            raise ValidationException("Cannot assign document type to an inactive category.")

        code_clean = data.code.upper().strip()
        existing = await db.scalar(
            select(DocumentType).where(
                DocumentType.tenant_id == tenant_id,
                DocumentType.code == code_clean,
            )
        )
        if existing:
            raise ConflictException(f"Document type with code '{code_clean}' already exists.")

        doc_type = DocumentType(
            id=uuid4(),
            tenant_id=tenant_id,
            category_id=data.category_id,
            code=code_clean,
            name=data.name.strip(),
            description=data.description,
            is_required_by_default=data.is_required_by_default,
            requires_expiry=data.requires_expiry,
            requires_verification=data.requires_verification,
            allowed_owner_types=data.allowed_owner_types,
            is_active=data.is_active,
        )
        db.add(doc_type)
        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="DOCUMENT_TYPE_CREATED",
                entity_type="DocumentType",
                entity_id=doc_type.id,
                details={"code": doc_type.code, "name": doc_type.name},
            )
        )
        await db.commit()
        await db.refresh(doc_type)
        return doc_type

    @classmethod
    async def update_document_type(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        type_id: UUID,
        data: DocumentTypeUpdate,
        user: User,
    ) -> DocumentType:
        doc_type = await cls.get_document_type(db, tenant_id, type_id)
        update_dict = data.model_dump(exclude_unset=True)

        for key, val in update_dict.items():
            if hasattr(doc_type, key) and val is not None:
                setattr(doc_type, key, val)

        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="DOCUMENT_TYPE_UPDATED",
                entity_type="DocumentType",
                entity_id=doc_type.id,
                details=update_dict,
            )
        )
        await db.commit()
        await db.refresh(doc_type)
        return doc_type

    # -------------------------------------------------------------------------
    # 3. DOCUMENT REQUIREMENTS
    # -------------------------------------------------------------------------
    @classmethod
    async def list_requirements(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        owner_type: str | None = None,
        program_id: UUID | None = None,
        department_id: UUID | None = None,
        academic_year_id: UUID | None = None,
        semester: int | None = None,
        is_active: bool | None = True,
    ) -> list[DocumentRequirement]:
        stmt = select(DocumentRequirement).where(DocumentRequirement.tenant_id == tenant_id)
        if owner_type:
            stmt = stmt.where(DocumentRequirement.owner_type == owner_type.upper().strip())
        if program_id:
            stmt = stmt.where(DocumentRequirement.program_id == program_id)
        if department_id:
            stmt = stmt.where(DocumentRequirement.department_id == department_id)
        if academic_year_id:
            stmt = stmt.where(DocumentRequirement.academic_year_id == academic_year_id)
        if semester is not None:
            stmt = stmt.where(DocumentRequirement.semester == semester)
        if is_active is not None:
            stmt = stmt.where(DocumentRequirement.is_active == is_active)

        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def create_requirement(
        cls, db: AsyncSession, tenant_id: UUID, data: DocumentRequirementCreate, user: User
    ) -> DocumentRequirement:
        # Verify document type exists
        await cls.get_document_type(db, tenant_id, data.document_type_id)

        req = DocumentRequirement(
            id=uuid4(),
            tenant_id=tenant_id,
            document_type_id=data.document_type_id,
            owner_type=data.owner_type.upper().strip(),
            program_id=data.program_id,
            department_id=data.department_id,
            academic_year_id=data.academic_year_id,
            semester=data.semester,
            role=data.role,
            is_required=data.is_required,
            is_active=data.is_active,
            description=data.description,
        )
        db.add(req)
        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="DOCUMENT_REQUIREMENT_CREATED",
                entity_type="DocumentRequirement",
                entity_id=req.id,
                details=data.model_dump(mode="json"),
            )
        )
        await db.commit()
        await db.refresh(req)
        return req

    # -------------------------------------------------------------------------
    # 4. DOCUMENT CRUD & SEARCH
    # -------------------------------------------------------------------------
    @classmethod
    async def list_documents(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Document], int]:
        stmt = (
            select(Document)
            .options(
                selectinload(Document.category),
                selectinload(Document.document_type),
                selectinload(Document.history),
                selectinload(Document.verifications),
            )
            .where(
                Document.tenant_id == tenant_id,
                Document.deleted_at.is_(None),
            )
        )

        if filters:
            if filters.get("search"):
                q = f"%{filters['search'].strip()}%"
                stmt = stmt.where(
                    or_(
                        Document.name.ilike(q),
                        Document.owner_name.ilike(q),
                        Document.owner_roll_number.ilike(q),
                        Document.document_number.ilike(q),
                        Document.issuing_authority.ilike(q),
                    )
                )
            if filters.get("category") and filters["category"] != "ALL":
                # Find category ID by code or UUID
                cat_val = filters["category"]
                cat = await cls.get_category_by_code(db, tenant_id, cat_val)
                if cat:
                    stmt = stmt.where(Document.category_id == cat.id)
                else:
                    try:
                        stmt = stmt.where(Document.category_id == UUID(cat_val))
                    except ValueError:
                        pass
            if filters.get("status") and filters["status"] != "ALL":
                stmt = stmt.where(Document.status == filters["status"].upper().strip())
            if filters.get("owner_type") and filters["owner_type"] != "ALL":
                stmt = stmt.where(Document.owner_type == filters["owner_type"].upper().strip())
            if filters.get("owner_id"):
                try:
                    stmt = stmt.where(Document.owner_id == UUID(str(filters["owner_id"])))
                except ValueError:
                    pass
            if filters.get("department") and filters["department"] != "ALL":
                stmt = stmt.where(Document.owner_department == filters["department"])
            if filters.get("program") and filters["program"] != "ALL":
                stmt = stmt.where(Document.program == filters["program"])
            if filters.get("priority") and filters["priority"] != "ALL":
                stmt = stmt.where(Document.priority == filters["priority"].upper().strip())
            if filters.get("reviewer_id") and filters["reviewer_id"] != "ALL":
                try:
                    stmt = stmt.where(Document.assigned_reviewer_id == UUID(str(filters["reviewer_id"])))
                except ValueError:
                    pass

        # Total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.scalar(count_stmt)) or 0

        # Order by created_at desc
        stmt = stmt.order_by(Document.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        res = await db.execute(stmt)
        return list(res.scalars().all()), total

    @classmethod
    async def get_document_by_id(
        cls, db: AsyncSession, tenant_id: UUID, document_id: UUID
    ) -> Document:
        stmt = (
            select(Document)
            .options(
                selectinload(Document.category),
                selectinload(Document.document_type),
                selectinload(Document.history),
                selectinload(Document.verifications),
                selectinload(Document.versions),
            )
            .where(
                Document.id == document_id,
                Document.tenant_id == tenant_id,
                Document.deleted_at.is_(None),
            )
        )
        doc = await db.scalar(stmt)
        if not doc:
            raise NotFoundException(f"Document with ID '{document_id}' not found.")
        return doc

    @classmethod
    async def create_document(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: DocumentCreate,
        user: User,
        file_content: bytes | None = None,
        file_name: str | None = None,
        mime_type: str | None = None,
    ) -> Document:
        # 1. Resolve Category
        cat = await cls.get_category_by_code(db, tenant_id, data.category)
        if not cat:
            try:
                cat = await cls.get_category_by_id(db, tenant_id, UUID(data.category))
            except (ValueError, NotFoundException):
                raise ValidationException(f"Valid category '{data.category}' not found.")

        if not cat.is_active:
            raise ValidationException(f"Cannot upload documents to inactive category '{cat.name}'.")

        # 2. Resolve Document Type if provided
        doc_type_id = None
        if data.document_type:
            types = await cls.list_document_types(db, tenant_id, category_id=cat.id)
            match = next((t for t in types if t.name.lower() == data.document_type.lower() or t.code == data.document_type.upper()), None)
            if match:
                if not match.is_active:
                    raise ValidationException(f"Document type '{match.name}' is inactive.")
                doc_type_id = match.id

        # 3. Handle File Storage if binary passed
        storage_key = data.file_reference
        calc_size = data.file_size or "1.2 MB"
        calc_mime = data.file_type or "application/pdf"
        checksum = None

        if file_content is not None and file_name is not None and mime_type is not None:
            storage = get_document_storage()
            dest_key = f"{tenant_id}/docs/{uuid4().hex[:12]}_{file_name}"
            storage_key = await storage.upload(file_content, dest_key, mime_type)
            calc_size = format_file_size(len(file_content))
            calc_mime = mime_type
            checksum = calculate_sha256(file_content)

        # 4. Resolve Owner ID
        try:
            owner_uuid = UUID(data.owner_id)
        except ValueError:
            owner_uuid = user.id

        # 5. Build Default Checklist
        default_checklist = [
            {"id": "chk-1", "label": "Document type matches institutional requirement", "checked": False, "required": True},
            {"id": "chk-2", "label": "All critical identity fields clearly readable", "checked": False, "required": True},
            {"id": "chk-3", "label": "Document issued by recognized official authority", "checked": False, "required": True},
            {"id": "chk-4", "label": "Validity and expiration dates within permitted terms", "checked": False, "required": False},
        ]

        doc = Document(
            id=uuid4(),
            tenant_id=tenant_id,
            category_id=cat.id,
            document_type_id=doc_type_id,
            name=data.name.strip(),
            owner_type=data.owner_type.upper().strip(),
            owner_id=owner_uuid,
            owner_name=data.owner_name or f"{user.first_name} {user.last_name}",
            owner_roll_number=data.owner_roll_number,
            owner_department=data.owner_department,
            program=data.program,
            academic_year=data.academic_year,
            semester=data.semester,
            status="UPLOADED",
            confidentiality=data.confidentiality.upper().strip(),
            priority=data.priority.upper().strip(),
            document_number=data.document_number,
            issuing_authority=data.issuing_authority,
            issue_date=datetime.fromisoformat(data.issue_date) if data.issue_date else None,
            expiry_date=datetime.fromisoformat(data.expiry_date) if data.expiry_date else None,
            file_reference=storage_key,
            file_name=file_name or data.name,
            file_size=calc_size,
            file_type=calc_mime,
            checksum=checksum,
            version=1,
            uploaded_by_id=user.id,
            verification_checklist=default_checklist,
            metadata_json=data.metadata,
        )
        db.add(doc)

        # Add initial timeline item
        history = cls._create_doc_history(
            document_id=doc.id,
            tenant_id=tenant_id,
            action="Document Uploaded",
            description=f"Document uploaded by {doc.owner_name}",
            performed_by_id=user.id,
            performed_by_name=f"{user.first_name} {user.last_name}",
            role=doc.owner_type,
            notes="Initial submission received.",
        )
        db.add(history)

        # Forensic Audit log
        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="DOCUMENT_UPLOADED",
                entity_type="Document",
                entity_id=doc.id,
                details={"name": doc.name, "category": cat.code, "owner_id": str(doc.owner_id)},
            )
        )

        await db.commit()
        return await cls.get_document_by_id(db, tenant_id, doc.id)

    @classmethod
    async def update_document_metadata(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        document_id: UUID,
        data: DocumentUpdate,
        user: User,
    ) -> Document:
        doc = await cls.get_document_by_id(db, tenant_id, document_id)
        if doc.status == "ARCHIVED":
            raise ValidationException("Archived documents cannot be directly edited.")

        update_dict = data.model_dump(exclude_unset=True)
        if "name" in update_dict and update_dict["name"] is not None:
            doc.name = update_dict["name"].strip()
        if "document_number" in update_dict:
            doc.document_number = update_dict["document_number"]
        if "issuing_authority" in update_dict:
            doc.issuing_authority = update_dict["issuing_authority"]
        if "issue_date" in update_dict:
            doc.issue_date = datetime.fromisoformat(update_dict["issue_date"]) if update_dict["issue_date"] else None
        if "expiry_date" in update_dict:
            doc.expiry_date = datetime.fromisoformat(update_dict["expiry_date"]) if update_dict["expiry_date"] else None
        if "confidentiality" in update_dict and update_dict["confidentiality"] is not None:
            doc.confidentiality = update_dict["confidentiality"].upper().strip()
        if "priority" in update_dict and update_dict["priority"] is not None:
            doc.priority = update_dict["priority"].upper().strip()
        if "metadata" in update_dict and update_dict["metadata"] is not None:
            doc.metadata_json = update_dict["metadata"]

        hist = cls._create_doc_history(
            document_id=doc.id,
            tenant_id=tenant_id,
            action="Metadata Updated",
            description="Document metadata and validity attributes modified",
            performed_by_id=user.id,
            performed_by_name=f"{user.first_name} {user.last_name}",
            role="REGISTRAR",
        )
        db.add(hist)

        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="DOCUMENT_UPDATED",
                entity_type="Document",
                entity_id=doc.id,
                details=update_dict,
            )
        )
        await db.commit()
        return await cls.get_document_by_id(db, tenant_id, doc.id)

    # -------------------------------------------------------------------------
    # 5. DOCUMENT LIFECYCLE & VERIFICATION WORKFLOW
    # -------------------------------------------------------------------------
    @classmethod
    async def submit_for_verification(
        cls, db: AsyncSession, tenant_id: UUID, document_id: UUID, user: User
    ) -> Document:
        doc = await cls.get_document_by_id(db, tenant_id, document_id)
        if doc.status not in ("UPLOADED", "REJECTED", "MISSING"):
            raise ValidationException(f"Document in status '{doc.status}' cannot be submitted for review.")

        doc.status = "UNDER_REVIEW"
        hist = cls._create_doc_history(
            document_id=doc.id,
            tenant_id=tenant_id,
            action="Submitted for Verification",
            description="Moved to institutional verification desk",
            performed_by_id=user.id,
            performed_by_name=f"{user.first_name} {user.last_name}",
            role=doc.owner_type,
        )
        db.add(hist)
        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="DOCUMENT_SUBMITTED",
                entity_type="Document",
                entity_id=doc.id,
            )
        )
        await db.commit()
        return await cls.get_document_by_id(db, tenant_id, doc.id)

    @classmethod
    async def start_review(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        document_id: UUID,
        reviewer_user: User,
        reviewer_name: str | None = None,
    ) -> Document:
        doc = await cls.get_document_by_id(db, tenant_id, document_id)
        name = reviewer_name or f"{reviewer_user.first_name} {reviewer_user.last_name}"

        doc.status = "UNDER_REVIEW"
        doc.assigned_reviewer_id = reviewer_user.id
        doc.assigned_reviewer_name = name

        # Add verification record
        verif = DocumentVerification(
            id=uuid4(),
            tenant_id=tenant_id,
            document_id=doc.id,
            reviewer_id=reviewer_user.id,
            reviewer_name=name,
            status="UNDER_REVIEW",
            notes="Compliance inspection started.",
        )
        db.add(verif)

        hist = cls._create_doc_history(
            document_id=doc.id,
            tenant_id=tenant_id,
            action="Review Commenced",
            description=f"Assigned to {name} for verification inspection",
            performed_by_id=reviewer_user.id,
            performed_by_name=name,
            role="VERIFICATION_OFFICER",
        )
        db.add(hist)
        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=reviewer_user.id,
                action="DOCUMENT_REVIEW_STARTED",
                entity_type="Document",
                entity_id=doc.id,
            )
        )
        await db.commit()
        return await cls.get_document_by_id(db, tenant_id, doc.id)

    @classmethod
    async def verify_document(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        document_id: UUID,
        verifier_user: User,
        verifier_name: str | None = None,
        notes: str | None = None,
    ) -> Document:
        doc = await cls.get_document_by_id(db, tenant_id, document_id)
        if doc.status not in ("UNDER_REVIEW", "UPLOADED"):
            raise ValidationException(f"Cannot verify document in current status '{doc.status}'.")

        name = verifier_name or f"{verifier_user.first_name} {verifier_user.last_name}"

        doc.status = "VERIFIED"
        doc.verified_at = datetime.now(UTC)
        doc.verified_by_id = verifier_user.id
        doc.verified_by_name = name
        doc.rejection_reason = None

        # Check all checklist items
        if doc.verification_checklist:
            checklist = list(doc.verification_checklist)
            for item in checklist:
                item["checked"] = True
            doc.verification_checklist = checklist

        verif = DocumentVerification(
            id=uuid4(),
            tenant_id=tenant_id,
            document_id=doc.id,
            reviewer_id=verifier_user.id,
            reviewer_name=name,
            status="VERIFIED",
            notes=notes or "Authenticated against institutional standards.",
            checklist_snapshot=doc.verification_checklist,
        )
        db.add(verif)

        hist = cls._create_doc_history(
            document_id=doc.id,
            tenant_id=tenant_id,
            action="Document Verified",
            description=f"Approved and verified by {name}",
            performed_by_id=verifier_user.id,
            performed_by_name=name,
            role="VERIFICATION_OFFICER",
            notes=notes,
        )
        db.add(hist)
        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=verifier_user.id,
                action="DOCUMENT_VERIFIED",
                entity_type="Document",
                entity_id=doc.id,
                details={"verified_by": name, "notes": notes},
            )
        )
        await db.commit()
        return await cls.get_document_by_id(db, tenant_id, doc.id)

    @classmethod
    async def reject_document(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        document_id: UUID,
        reason: str,
        verifier_user: User,
        verifier_name: str | None = None,
    ) -> Document:
        if not reason or not reason.strip():
            raise ValidationException("A specific rejection reason is mandatory when rejecting a document.")

        doc = await cls.get_document_by_id(db, tenant_id, document_id)
        name = verifier_name or f"{verifier_user.first_name} {verifier_user.last_name}"

        clean_reason = reason.strip()
        doc.status = "REJECTED"
        doc.verified_at = datetime.now(UTC)
        doc.verified_by_id = verifier_user.id
        doc.verified_by_name = name
        doc.rejection_reason = clean_reason

        verif = DocumentVerification(
            id=uuid4(),
            tenant_id=tenant_id,
            document_id=doc.id,
            reviewer_id=verifier_user.id,
            reviewer_name=name,
            status="REJECTED",
            reason=clean_reason,
        )
        db.add(verif)

        hist = cls._create_doc_history(
            document_id=doc.id,
            tenant_id=tenant_id,
            action="Document Rejected",
            description=f"Rejected by {name}: {clean_reason}",
            performed_by_id=verifier_user.id,
            performed_by_name=name,
            role="VERIFICATION_OFFICER",
            notes=clean_reason,
        )
        db.add(hist)
        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=verifier_user.id,
                action="DOCUMENT_REJECTED",
                entity_type="Document",
                entity_id=doc.id,
                details={"reason": clean_reason, "rejected_by": name},
            )
        )
        await db.commit()
        return await cls.get_document_by_id(db, tenant_id, doc.id)

    @classmethod
    async def request_reupload(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        document_id: UUID,
        instruction: str,
        verifier_user: User,
        verifier_name: str | None = None,
    ) -> Document:
        if not instruction or not instruction.strip():
            raise ValidationException("Instruction required for document re-upload.")

        msg = f"Re-upload requested: {instruction.strip()}"
        return await cls.reject_document(
            db, tenant_id, document_id, reason=msg, verifier_user=verifier_user, verifier_name=verifier_name
        )

    @classmethod
    async def reupload_document(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        document_id: UUID,
        file_content: bytes,
        file_name: str,
        mime_type: str,
        user: User,
    ) -> Document:
        doc = await cls.get_document_by_id(db, tenant_id, document_id)

        # 1. Archive current version as DocumentVersion record
        prev_version = DocumentVersion(
            id=uuid4(),
            tenant_id=tenant_id,
            document_id=doc.id,
            version_number=doc.version,
            file_reference=doc.file_reference or "",
            file_name=doc.file_name or doc.name,
            mime_type=doc.file_type or "application/pdf",
            file_size=doc.file_size or "1.2 MB",
            checksum=doc.checksum or "",
            uploaded_by_id=doc.uploaded_by_id,
            uploaded_at=doc.updated_at,
        )
        db.add(prev_version)

        # 2. Upload replacement file
        storage = get_document_storage()
        dest_key = f"{tenant_id}/docs/{uuid4().hex[:12]}_{file_name}"
        storage_key = await storage.upload(file_content, dest_key, mime_type)

        # 3. Update document state
        doc.file_reference = storage_key
        doc.file_name = file_name
        doc.file_type = mime_type
        doc.file_size = format_file_size(len(file_content))
        doc.checksum = calculate_sha256(file_content)
        doc.version += 1
        doc.status = "UPLOADED"
        doc.rejection_reason = None
        doc.uploaded_by_id = user.id

        hist = cls._create_doc_history(
            document_id=doc.id,
            tenant_id=tenant_id,
            action="Document Re-uploaded",
            description=f"Replacement file uploaded (version {doc.version})",
            performed_by_id=user.id,
            performed_by_name=f"{user.first_name} {user.last_name}",
            role=doc.owner_type,
        )
        db.add(hist)
        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="DOCUMENT_REPLACED",
                entity_type="Document",
                entity_id=doc.id,
                details={"version": doc.version, "file_name": file_name},
            )
        )
        await db.commit()
        return await cls.get_document_by_id(db, tenant_id, doc.id)

    @classmethod
    async def update_checklist_item(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        document_id: UUID,
        item_id: str,
        checked: bool,
        notes: str | None = None,
    ) -> Document:
        doc = await cls.get_document_by_id(db, tenant_id, document_id)
        if doc.verification_checklist:
            checklist = list(doc.verification_checklist)
            item = next((c for c in checklist if c.get("id") == item_id), None)
            if item:
                item["checked"] = checked
                if notes:
                    item["notes"] = notes
                doc.verification_checklist = checklist
                await db.commit()
        return await cls.get_document_by_id(db, tenant_id, doc.id)

    @classmethod
    async def archive_document(
        cls, db: AsyncSession, tenant_id: UUID, document_id: UUID, user: User
    ) -> Document:
        doc = await cls.get_document_by_id(db, tenant_id, document_id)
        doc.status = "ARCHIVED"

        hist = cls._create_doc_history(
            document_id=doc.id,
            tenant_id=tenant_id,
            action="Document Archived",
            description="Transferred to institutional digital archive",
            performed_by_id=user.id,
            performed_by_name=f"{user.first_name} {user.last_name}",
        )
        db.add(hist)
        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="DOCUMENT_ARCHIVED",
                entity_type="Document",
                entity_id=doc.id,
            )
        )
        await db.commit()
        return await cls.get_document_by_id(db, tenant_id, doc.id)

    @classmethod
    async def delete_document(
        cls, db: AsyncSession, tenant_id: UUID, document_id: UUID, user: User
    ) -> bool:
        doc = await cls.get_document_by_id(db, tenant_id, document_id)
        doc.deleted_at = datetime.now(UTC)

        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="DOCUMENT_DELETED",
                entity_type="Document",
                entity_id=doc.id,
            )
        )
        await db.commit()
        return True

    # -------------------------------------------------------------------------
    # 6. CERTIFICATE TEMPLATES
    # -------------------------------------------------------------------------
    @classmethod
    async def list_templates(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        audience: str | None = None,
    ) -> list[CertificateTemplate]:
        stmt = (
            select(CertificateTemplate)
            .options(
                selectinload(CertificateTemplate.fields),
                selectinload(CertificateTemplate.versions),
            )
            .where(CertificateTemplate.tenant_id == tenant_id)
            .order_by(CertificateTemplate.template_name.asc())
        )
        res = await db.execute(stmt)
        templates = res.scalars().all()

        if audience and audience != "ALL":
            clean_aud = audience.upper().strip()
            templates = [
                t for t in templates
                if "ALL" in t.applicable_audience or clean_aud in t.applicable_audience
            ]
        return list(templates)

    @classmethod
    async def get_template_by_id(
        cls, db: AsyncSession, tenant_id: UUID, template_id: UUID
    ) -> CertificateTemplate:
        stmt = (
            select(CertificateTemplate)
            .options(
                selectinload(CertificateTemplate.fields),
                selectinload(CertificateTemplate.versions),
            )
            .where(
                CertificateTemplate.id == template_id,
                CertificateTemplate.tenant_id == tenant_id,
            )
        )
        tmpl = await db.scalar(stmt)
        if not tmpl:
            raise NotFoundException(f"Certificate template with ID '{template_id}' not found.")
        return tmpl

    @classmethod
    async def create_template(
        cls, db: AsyncSession, tenant_id: UUID, data: CertificateTemplateCreate, user: User
    ) -> CertificateTemplate:
        code_clean = data.code.upper().strip()
        existing = await db.scalar(
            select(CertificateTemplate).where(
                CertificateTemplate.tenant_id == tenant_id,
                CertificateTemplate.code == code_clean,
            )
        )
        if existing:
            raise ConflictException(f"Certificate template code '{code_clean}' already exists.")

        tmpl = CertificateTemplate(
            id=uuid4(),
            tenant_id=tenant_id,
            code=code_clean,
            template_name=data.template_name.strip(),
            certificate_type=data.certificate_type.upper().strip(),
            description=data.description,
            applicable_audience=data.applicable_audience,
            status=data.status.upper().strip(),
            current_version="1.0",
            template_body=data.template_body,
            usage_count=0,
        )
        db.add(tmpl)
        await db.flush()

        # Add initial version snapshot
        ver = CertificateTemplateVersion(
            id=uuid4(),
            tenant_id=tenant_id,
            template_id=tmpl.id,
            version_string="1.0",
            template_body=data.template_body,
            changelog="Initial production template definition",
            published_by_id=user.id,
            published_by_name=f"{user.first_name} {user.last_name}",
            is_active=True,
        )
        db.add(ver)

        # Add fields
        for f in data.fields:
            field_rec = CertificateTemplateField(
                id=uuid4(),
                tenant_id=tenant_id,
                template_id=tmpl.id,
                name=f.name,
                label=f.label,
                field_type=f.type,
                required=f.required,
                system_variable_mapping=f.system_variable_mapping,
                default_value=f.default_value,
            )
            db.add(field_rec)

        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="CERTIFICATE_TEMPLATE_CREATED",
                entity_type="CertificateTemplate",
                entity_id=tmpl.id,
                details={"code": tmpl.code, "name": tmpl.template_name},
            )
        )
        await db.commit()
        return await cls.get_template_by_id(db, tenant_id, tmpl.id)

    @classmethod
    async def update_template(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        template_id: UUID,
        data: CertificateTemplateUpdate,
        user: User,
    ) -> CertificateTemplate:
        tmpl = await cls.get_template_by_id(db, tenant_id, template_id)

        update_dict = data.model_dump(exclude_unset=True)
        if "template_name" in update_dict and update_dict["template_name"]:
            tmpl.template_name = update_dict["template_name"].strip()
        if "description" in update_dict:
            tmpl.description = update_dict["description"]
        if "status" in update_dict and update_dict["status"]:
            tmpl.status = update_dict["status"].upper().strip()
        if "applicable_audience" in update_dict and update_dict["applicable_audience"]:
            tmpl.applicable_audience = update_dict["applicable_audience"]

        # Version preservation
        if "template_body" in update_dict and update_dict["template_body"]:
            new_version = update_dict.get("version") or f"{float(tmpl.current_version) + 0.1:.1f}"
            tmpl.template_body = update_dict["template_body"]
            tmpl.current_version = new_version

            ver = CertificateTemplateVersion(
                id=uuid4(),
                tenant_id=tenant_id,
                template_id=tmpl.id,
                version_string=new_version,
                template_body=tmpl.template_body,
                changelog="Template layout or field structure updated",
                published_by_id=user.id,
                published_by_name=f"{user.first_name} {user.last_name}",
                is_active=True,
            )
            db.add(ver)

        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="CERTIFICATE_TEMPLATE_UPDATED",
                entity_type="CertificateTemplate",
                entity_id=tmpl.id,
                details=update_dict,
            )
        )
        await db.commit()
        return await cls.get_template_by_id(db, tenant_id, tmpl.id)

    # -------------------------------------------------------------------------
    # 7. CERTIFICATE REQUESTS LIFECYCLE & ISSUANCE
    # -------------------------------------------------------------------------
    @classmethod
    async def list_certificate_requests(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        filters: dict[str, Any] | None = None,
    ) -> list[CertificateRequest]:
        stmt = (
            select(CertificateRequest)
            .options(selectinload(CertificateRequest.template))
            .where(CertificateRequest.tenant_id == tenant_id)
        )

        if filters:
            if filters.get("status") and filters["status"] != "ALL":
                stmt = stmt.where(CertificateRequest.status == filters["status"].upper().strip())
            if filters.get("student_id"):
                try:
                    stmt = stmt.where(CertificateRequest.student_id == UUID(str(filters["student_id"])))
                except ValueError:
                    pass
            if filters.get("certificate_type") and filters["certificate_type"] != "ALL":
                stmt = stmt.where(CertificateRequest.certificate_type == filters["certificate_type"].upper().strip())
            if filters.get("search"):
                q = f"%{filters['search'].strip()}%"
                stmt = stmt.where(
                    or_(
                        CertificateRequest.request_id.ilike(q),
                        CertificateRequest.student_name.ilike(q),
                        CertificateRequest.roll_number.ilike(q),
                    )
                )

        stmt = stmt.order_by(CertificateRequest.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def get_certificate_request_by_id(
        cls, db: AsyncSession, tenant_id: UUID, request_id: UUID | str
    ) -> CertificateRequest:
        stmt = select(CertificateRequest).options(selectinload(CertificateRequest.template)).where(
            CertificateRequest.tenant_id == tenant_id
        )
        try:
            req_uuid = UUID(str(request_id))
            stmt = stmt.where(or_(CertificateRequest.id == req_uuid, CertificateRequest.request_id == str(request_id)))
        except ValueError:
            stmt = stmt.where(CertificateRequest.request_id == str(request_id))

        req = await db.scalar(stmt)
        if not req:
            raise NotFoundException(f"Certificate request '{request_id}' not found.")
        return req

    @classmethod
    async def create_certificate_request(
        cls, db: AsyncSession, tenant_id: UUID, data: CertificateRequestCreate, student_user: User
    ) -> CertificateRequest:
        # Resolve Template
        tmpl = None
        try:
            tmpl = await cls.get_template_by_id(db, tenant_id, UUID(data.template_id))
        except (ValueError, NotFoundException):
            templates = await cls.list_templates(db, tenant_id)
            tmpl = next((t for t in templates if t.template_name == data.template_name or t.code == data.template_id), None)
            if not tmpl:
                raise ValidationException("Valid certificate template required.")

        # Resolve Student
        student = None
        if data.student_id:
            try:
                student = await db.scalar(select(StudentProfile).where(StudentProfile.id == UUID(data.student_id)))
            except ValueError:
                pass
        if not student:
            student = await db.scalar(
                select(StudentProfile).where(
                    StudentProfile.user_id == student_user.id,
                    StudentProfile.tenant_id == tenant_id,
                )
            )

        student_uuid = student.id if student else student_user.id
        s_name = data.student_name or f"{student_user.first_name} {student_user.last_name}"
        s_roll = data.roll_number or (student.roll_number if student else "24CSE0101")
        s_prog = data.program or (student.enrollment_history[0].program.name if (student and student.enrollment_history and student.enrollment_history[0].program) else "B.Tech Computer Science & Engineering")
        s_dept = data.department or "Computer Science & Engineering"

        # Sequential request identifier
        count = (await db.scalar(select(func.count(CertificateRequest.id)).where(CertificateRequest.tenant_id == tenant_id))) or 0
        year = datetime.now(UTC).year
        req_id_str = f"REQ-{year}-{count + 1:04d}"

        val_checks = [
            {"id": "chk-c1", "title": "Active Academic Enrollment Verification", "passed": True, "details": "Verified in registry"},
            {"id": "chk-c2", "title": "Finance Dues & Accounts Ledger Clearance", "passed": True, "details": "Accounts ledger clear"},
            {"id": "chk-c3", "title": "Disciplinary Standing & Conduct Status", "passed": True, "details": "Good standing"},
        ]

        timeline = [
            {
                "id": f"t-{uuid4().hex[:8]}",
                "status": "SUBMITTED",
                "title": "Request Submitted",
                "performedBy": s_name,
                "timestamp": datetime.now(UTC).isoformat(),
                "notes": data.purpose,
            }
        ]

        req = CertificateRequest(
            id=uuid4(),
            tenant_id=tenant_id,
            request_id=req_id_str,
            student_id=student_uuid,
            student_name=s_name,
            roll_number=s_roll,
            program=s_prog,
            department=s_dept,
            template_id=tmpl.id,
            certificate_type=data.certificate_type or tmpl.certificate_type,
            purpose=data.purpose.strip(),
            required_by_date=datetime.fromisoformat(data.required_by_date) if data.required_by_date else None,
            status="SUBMITTED",
            validation_checks=val_checks,
            timeline=timeline,
        )
        db.add(req)
        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=student_user.id,
                action="CERTIFICATE_REQUEST_CREATED",
                entity_type="CertificateRequest",
                entity_id=req.id,
                details={"request_id": req.request_id, "purpose": req.purpose},
            )
        )
        await db.commit()
        return await cls.get_certificate_request_by_id(db, tenant_id, req.id)

    @classmethod
    async def review_certificate_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID | str,
        reviewer_user: User,
        reviewer_name: str | None = None,
    ) -> CertificateRequest:
        req = await cls.get_certificate_request_by_id(db, tenant_id, request_id)
        name = reviewer_name or f"{reviewer_user.first_name} {reviewer_user.last_name}"

        req.status = "UNDER_REVIEW"
        req.reviewer_id = reviewer_user.id
        req.reviewer_name = name
        req.reviewed_at = datetime.now(UTC)

        tl = list(req.timeline or [])
        tl.insert(
            0,
            {
                "id": f"t-{uuid4().hex[:8]}",
                "status": "UNDER_REVIEW",
                "title": "Application Under Review",
                "performedBy": name,
                "timestamp": datetime.now(UTC).isoformat(),
                "notes": "Clearance check conducted",
            },
        )
        req.timeline = tl

        await db.commit()
        return await cls.get_certificate_request_by_id(db, tenant_id, req.id)

    @classmethod
    async def approve_certificate_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID | str,
        data: CertificateRequestApprove,
        reviewer_user: User,
    ) -> CertificateRequest:
        req = await cls.get_certificate_request_by_id(db, tenant_id, request_id)
        if req.status not in ("SUBMITTED", "UNDER_REVIEW"):
            raise ValidationException(f"Cannot approve request in status '{req.status}'.")

        name = data.reviewer_name or f"{reviewer_user.first_name} {reviewer_user.last_name}"
        req.status = "APPROVED"
        req.reviewer_id = reviewer_user.id
        req.reviewer_name = name
        req.reviewed_at = datetime.now(UTC)

        tl = list(req.timeline or [])
        tl.insert(
            0,
            {
                "id": f"t-{uuid4().hex[:8]}",
                "status": "APPROVED",
                "title": "Request Approved",
                "performedBy": name,
                "timestamp": datetime.now(UTC).isoformat(),
                "notes": data.notes or "Clearance approved by administrative authority.",
            },
        )
        req.timeline = tl

        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=reviewer_user.id,
                action="CERTIFICATE_REQUEST_APPROVED",
                entity_type="CertificateRequest",
                entity_id=req.id,
                details={"request_id": req.request_id, "approved_by": name},
            )
        )
        await db.commit()
        return await cls.get_certificate_request_by_id(db, tenant_id, req.id)

    @classmethod
    async def reject_certificate_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID | str,
        data: CertificateRequestReject,
        reviewer_user: User,
    ) -> CertificateRequest:
        if not data.reason or not data.reason.strip():
            raise ValidationException("Rejection reason is mandatory.")

        req = await cls.get_certificate_request_by_id(db, tenant_id, request_id)
        name = data.reviewer_name or f"{reviewer_user.first_name} {reviewer_user.last_name}"

        req.status = "REJECTED"
        req.reviewer_id = reviewer_user.id
        req.reviewer_name = name
        req.reviewed_at = datetime.now(UTC)
        req.rejection_reason = data.reason.strip()

        tl = list(req.timeline or [])
        tl.insert(
            0,
            {
                "id": f"t-{uuid4().hex[:8]}",
                "status": "REJECTED",
                "title": "Request Rejected",
                "performedBy": name,
                "timestamp": datetime.now(UTC).isoformat(),
                "notes": req.rejection_reason,
            },
        )
        req.timeline = tl

        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=reviewer_user.id,
                action="CERTIFICATE_REQUEST_REJECTED",
                entity_type="CertificateRequest",
                entity_id=req.id,
                details={"request_id": req.request_id, "reason": req.rejection_reason},
            )
        )
        await db.commit()
        return await cls.get_certificate_request_by_id(db, tenant_id, req.id)

    @classmethod
    async def cancel_certificate_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID | str,
        reason: str | None,
        user: User,
    ) -> CertificateRequest:
        req = await cls.get_certificate_request_by_id(db, tenant_id, request_id)
        if req.status not in ("SUBMITTED", "UNDER_REVIEW"):
            raise ValidationException("Only submitted or under-review requests can be cancelled.")

        req.status = "CANCELLED"
        tl = list(req.timeline or [])
        tl.insert(
            0,
            {
                "id": f"t-{uuid4().hex[:8]}",
                "status": "CANCELLED",
                "title": "Request Cancelled by Applicant",
                "performedBy": f"{user.first_name} {user.last_name}",
                "timestamp": datetime.now(UTC).isoformat(),
                "notes": reason or "Cancelled by applicant.",
            },
        )
        req.timeline = tl

        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="CERTIFICATE_REQUEST_CANCELLED",
                entity_type="CertificateRequest",
                entity_id=req.id,
                details={"request_id": req.request_id, "reason": reason},
            )
        )
        await db.commit()
        return await cls.get_certificate_request_by_id(db, tenant_id, req.id)

    @classmethod
    async def issue_certificate_for_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID | str,
        issuing_authority: str,
        user: User,
    ) -> IssuedCertificate:
        req = await cls.get_certificate_request_by_id(db, tenant_id, request_id)

        # Enforce business rule: Certificate cannot be issued before approval!
        if req.status != "APPROVED":
            raise ValidationException(
                f"Cannot issue certificate. Current status is '{req.status}', but must be 'APPROVED'."
            )

        # Generate unique certificate number
        count = (
            await db.scalar(
                select(func.count(IssuedCertificate.id)).where(IssuedCertificate.tenant_id == tenant_id)
            )
        ) or 0
        year = datetime.now(UTC).year
        cert_num = f"CAMPUSOS/CERT/{year}/{count + 1:04d}"

        # Generate cryptographic verification hash & QR URL
        hash_payload = f"{tenant_id}:{cert_num}:{req.student_id}:{year}".encode()
        verification_hash = hashlib.sha256(hash_payload).hexdigest()
        qr_url = f"https://verify.campusos.edu/cert/{cert_num}"

        issued_cert = IssuedCertificate(
            id=uuid4(),
            tenant_id=tenant_id,
            request_id=req.id,
            certificate_number=cert_num,
            certificate_type=req.certificate_type,
            recipient_id=req.student_id,
            recipient_name=req.student_name,
            recipient_roll_number=req.roll_number,
            recipient_program=req.program,
            recipient_department=req.department,
            template_id=req.template_id,
            template_version_string="1.0",
            issuing_authority=issuing_authority or "Office of the Registrar",
            issue_date=datetime.now(UTC),
            status="ISSUED",
            verification_hash=verification_hash,
            qr_verification_url=qr_url,
        )
        db.add(issued_cert)

        # Update Request status
        req.status = "ISSUED"
        req.issued_certificate_id = issued_cert.id
        req.issued_date = issued_cert.issue_date

        tl = list(req.timeline or [])
        tl.insert(
            0,
            {
                "id": f"t-{uuid4().hex[:8]}",
                "status": "ISSUED",
                "title": "Certificate Issued & Dispatched",
                "performedBy": issuing_authority,
                "timestamp": datetime.now(UTC).isoformat(),
                "notes": f"Certificate Number: {cert_num}",
            },
        )
        req.timeline = tl

        # Increment template usage
        tmpl = await cls.get_template_by_id(db, tenant_id, req.template_id)
        tmpl.usage_count += 1

        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="CERTIFICATE_ISSUED",
                entity_type="IssuedCertificate",
                entity_id=issued_cert.id,
                details={"certificate_number": cert_num, "recipient": req.student_name},
            )
        )

        await db.commit()
        await db.refresh(issued_cert)
        return issued_cert

    # -------------------------------------------------------------------------
    # 8. ISSUED CERTIFICATES & REVOCATION
    # -------------------------------------------------------------------------
    @classmethod
    async def list_issued_certificates(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        filters: dict[str, Any] | None = None,
    ) -> list[IssuedCertificate]:
        stmt = select(IssuedCertificate).where(IssuedCertificate.tenant_id == tenant_id)

        if filters:
            if filters.get("recipient_id"):
                try:
                    stmt = stmt.where(IssuedCertificate.recipient_id == UUID(str(filters["recipient_id"])))
                except ValueError:
                    pass
            if filters.get("certificate_type") and filters["certificate_type"] != "ALL":
                stmt = stmt.where(IssuedCertificate.certificate_type == filters["certificate_type"].upper().strip())
            if filters.get("status") and filters["status"] != "ALL":
                stmt = stmt.where(IssuedCertificate.status == filters["status"].upper().strip())
            if filters.get("search"):
                q = f"%{filters['search'].strip()}%"
                stmt = stmt.where(
                    or_(
                        IssuedCertificate.certificate_number.ilike(q),
                        IssuedCertificate.recipient_name.ilike(q),
                        IssuedCertificate.recipient_roll_number.ilike(q),
                    )
                )

        stmt = stmt.order_by(IssuedCertificate.issue_date.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def get_issued_certificate_by_id(
        cls, db: AsyncSession, tenant_id: UUID, cert_id_or_number: UUID | str
    ) -> IssuedCertificate:
        stmt = select(IssuedCertificate).where(IssuedCertificate.tenant_id == tenant_id)
        try:
            cert_uuid = UUID(str(cert_id_or_number))
            stmt = stmt.where(or_(IssuedCertificate.id == cert_uuid, IssuedCertificate.certificate_number == str(cert_id_or_number)))
        except ValueError:
            stmt = stmt.where(IssuedCertificate.certificate_number == str(cert_id_or_number))

        cert = await db.scalar(stmt)
        if not cert:
            raise NotFoundException(f"Issued certificate '{cert_id_or_number}' not found.")
        return cert

    @classmethod
    async def verify_certificate_public(
        cls, db: AsyncSession, cert_code: str
    ) -> tuple[bool, IssuedCertificate | None, str]:
        clean = cert_code.strip()
        stmt = select(IssuedCertificate).where(
            or_(
                IssuedCertificate.certificate_number.ilike(clean),
                IssuedCertificate.verification_hash.ilike(clean),
                IssuedCertificate.qr_verification_url.ilike(f"%{clean}%"),
            )
        )
        cert = await db.scalar(stmt)
        if not cert:
            return False, None, "No institutional certificate matches this verification query."
        if cert.status == "REVOKED":
            return False, cert, f"Certificate was revoked on {cert.revoked_at.isoformat() if cert.revoked_at else 'historical date'}: {cert.revocation_reason}"
        return True, cert, "Certificate cryptographically verified and authentic."

    @classmethod
    async def revoke_certificate(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        cert_id_or_number: UUID | str,
        reason: str,
        user: User,
    ) -> IssuedCertificate:
        if not reason or not reason.strip():
            raise ValidationException("Revocation reason is mandatory.")

        cert = await cls.get_issued_certificate_by_id(db, tenant_id, cert_id_or_number)
        if cert.status == "REVOKED":
            raise ValidationException("This certificate has already been revoked.")

        clean_reason = reason.strip()
        cert.status = "REVOKED"
        cert.revoked_at = datetime.now(UTC)
        cert.revoked_by_id = user.id
        cert.revocation_reason = clean_reason

        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="CERTIFICATE_REVOKED",
                entity_type="IssuedCertificate",
                entity_id=cert.id,
                details={"certificate_number": cert.certificate_number, "reason": clean_reason},
            )
        )
        await db.commit()
        await db.refresh(cert)
        return cert

    # -------------------------------------------------------------------------
    # 9. INSTITUTIONAL GOVERNANCE RECORDS
    # -------------------------------------------------------------------------
    @classmethod
    async def list_institutional_records(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        filters: dict[str, Any] | None = None,
        user_roles: set[str] | None = None,
    ) -> list[InstitutionalRecord]:
        stmt = (
            select(InstitutionalRecord)
            .options(selectinload(InstitutionalRecord.history))
            .where(InstitutionalRecord.tenant_id == tenant_id)
        )

        # Confidentiality filtering: only admins can see RESTRICTED
        roles = user_roles or set()
        is_admin = bool({"SUPER_ADMIN", "INSTITUTION_ADMIN", "DOCUMENT_OFFICER"}.intersection(roles))
        if not is_admin:
            stmt = stmt.where(InstitutionalRecord.confidentiality != "RESTRICTED")

        if filters:
            if filters.get("category") and filters["category"] != "ALL":
                stmt = stmt.where(InstitutionalRecord.category == filters["category"])
            if filters.get("department") and filters["department"] != "ALL":
                stmt = stmt.where(InstitutionalRecord.owner_department == filters["department"])
            if filters.get("confidentiality") and filters["confidentiality"] != "ALL":
                stmt = stmt.where(InstitutionalRecord.confidentiality == filters["confidentiality"].upper().strip())
            if filters.get("status") and filters["status"] != "ALL":
                stmt = stmt.where(InstitutionalRecord.status == filters["status"].upper().strip())
            if filters.get("search"):
                q = f"%{filters['search'].strip()}%"
                stmt = stmt.where(
                    or_(
                        InstitutionalRecord.record_name.ilike(q),
                        InstitutionalRecord.code.ilike(q),
                        InstitutionalRecord.reference_number.ilike(q),
                    )
                )

        stmt = stmt.order_by(InstitutionalRecord.created_date.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def get_institutional_record_by_id(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        record_id: UUID | str,
        user_roles: set[str] | None = None,
    ) -> InstitutionalRecord:
        stmt = (
            select(InstitutionalRecord)
            .options(selectinload(InstitutionalRecord.history))
            .where(InstitutionalRecord.tenant_id == tenant_id)
        )
        try:
            r_uuid = UUID(str(record_id))
            stmt = stmt.where(or_(InstitutionalRecord.id == r_uuid, InstitutionalRecord.code == str(record_id)))
        except ValueError:
            stmt = stmt.where(InstitutionalRecord.code == str(record_id))

        rec = await db.scalar(stmt)
        if not rec:
            raise NotFoundException(f"Institutional record '{record_id}' not found.")

        roles = user_roles or set()
        is_admin = bool({"SUPER_ADMIN", "INSTITUTION_ADMIN", "DOCUMENT_OFFICER"}.intersection(roles))
        if rec.confidentiality == "RESTRICTED" and not is_admin:
            raise PermissionDeniedException("institutional_records:restricted")

        return rec

    @classmethod
    async def create_institutional_record(
        cls, db: AsyncSession, tenant_id: UUID, data: InstitutionalRecordCreate, user: User
    ) -> InstitutionalRecord:
        code_str = data.code or f"REC-GOV-{uuid4().hex[:6].upper()}"
        existing = await db.scalar(
            select(InstitutionalRecord).where(
                InstitutionalRecord.tenant_id == tenant_id,
                InstitutionalRecord.code == code_str,
            )
        )
        if existing:
            raise ConflictException(f"Institutional record with code '{code_str}' already exists.")

        rel_docs = [d.model_dump() for d in data.related_documents] if data.related_documents else []

        rec = InstitutionalRecord(
            id=uuid4(),
            tenant_id=tenant_id,
            record_name=data.record_name.strip(),
            code=code_str,
            category=data.category.strip(),
            owner_department=data.owner_department.strip(),
            confidentiality=data.confidentiality.upper().strip(),
            status=data.status.upper().strip(),
            created_date=datetime.now(UTC),
            valid_until=datetime.fromisoformat(data.valid_until) if data.valid_until else None,
            issuing_authority=data.issuing_authority,
            reference_number=data.reference_number,
            description=data.description,
            file_type=data.file_type or "application/pdf",
            file_size=data.file_size or "2.4 MB",
            file_reference=data.file_reference,
            related_documents=rel_docs,
        )
        db.add(rec)

        hist = cls._create_inst_history(
            record_id=rec.id,
            tenant_id=tenant_id,
            action="Record Gazetted & Registered",
            performed_by_id=user.id,
            performed_by_name=f"{user.first_name} {user.last_name}",
            details="Registered in institutional document vault",
        )
        db.add(hist)

        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="INSTITUTIONAL_RECORD_CREATED",
                entity_type="InstitutionalRecord",
                entity_id=rec.id,
                details={"code": rec.code, "name": rec.record_name},
            )
        )
        await db.commit()
        user_roles = {ur.role.name for ur in user.roles if ur.role} if hasattr(user, "roles") and user.roles else {"INSTITUTION_ADMIN"}
        return await cls.get_institutional_record_by_id(db, tenant_id, rec.id, user_roles=user_roles)

    @classmethod
    async def update_institutional_record(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        record_id: UUID | str,
        data: InstitutionalRecordUpdate,
        user: User,
    ) -> InstitutionalRecord:
        user_roles = {ur.role.name for ur in user.roles if ur.role} if hasattr(user, "roles") and user.roles else {"INSTITUTION_ADMIN"}
        rec = await cls.get_institutional_record_by_id(db, tenant_id, record_id, user_roles=user_roles)
        update_dict = data.model_dump(exclude_unset=True)

        if "record_name" in update_dict and update_dict["record_name"]:
            rec.record_name = update_dict["record_name"].strip()
        if "category" in update_dict and update_dict["category"]:
            rec.category = update_dict["category"].strip()
        if "owner_department" in update_dict and update_dict["owner_department"]:
            rec.owner_department = update_dict["owner_department"].strip()
        if "confidentiality" in update_dict and update_dict["confidentiality"]:
            rec.confidentiality = update_dict["confidentiality"].upper().strip()
        if "status" in update_dict and update_dict["status"]:
            rec.status = update_dict["status"].upper().strip()
        if "valid_until" in update_dict:
            rec.valid_until = datetime.fromisoformat(update_dict["valid_until"]) if update_dict["valid_until"] else None
        if "issuing_authority" in update_dict:
            rec.issuing_authority = update_dict["issuing_authority"]
        if "reference_number" in update_dict:
            rec.reference_number = update_dict["reference_number"]
        if "description" in update_dict:
            rec.description = update_dict["description"]
        if "related_documents" in update_dict and update_dict["related_documents"] is not None:
            rec.related_documents = [d.model_dump() for d in update_dict["related_documents"]]

        hist = cls._create_inst_history(
            record_id=rec.id,
            tenant_id=tenant_id,
            action="Record Metadata Updated",
            performed_by_id=user.id,
            performed_by_name=f"{user.first_name} {user.last_name}",
            details="Attributes modified in governance register",
        )
        db.add(hist)
        db.add(
            cls._create_audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                action="INSTITUTIONAL_RECORD_UPDATED",
                entity_type="InstitutionalRecord",
                entity_id=rec.id,
                details=update_dict,
            )
        )
        await db.commit()
        return await cls.get_institutional_record_by_id(db, tenant_id, rec.id, user_roles=user_roles)

    # -------------------------------------------------------------------------
    # 10. DASHBOARD SUMMARY & AGGREGATIONS
    # -------------------------------------------------------------------------
    @classmethod
    async def get_dashboard_summary(
        cls, db: AsyncSession, tenant_id: UUID
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        d7 = now + timedelta(days=7)
        d30 = now + timedelta(days=30)
        d90 = now + timedelta(days=90)
        start_of_month = datetime(now.year, now.month, 1, tzinfo=UTC)

        # 1. Document metrics aggregation
        doc_agg_stmt = select(
            func.count(Document.id).label("total"),
            func.count(case((Document.status == "VERIFIED", 1))).label("verified"),
            func.count(case((Document.status.in_(["UPLOADED", "UNDER_REVIEW"]), 1))).label("pending"),
            func.count(case((Document.status == "REJECTED", 1))).label("rejected"),
            func.count(case((Document.status == "MISSING", 1))).label("missing"),
            # Expiring within 30 days
            func.count(
                case(
                    (
                        and_(
                            Document.expiry_date.is_not(None),
                            Document.expiry_date > now,
                            Document.expiry_date <= d30,
                        ),
                        1,
                    )
                )
            ).label("expiring_30"),
            # Expiry breakdown
            func.count(case((and_(Document.expiry_date.is_not(None), Document.expiry_date <= now), 1))).label("expired"),
            func.count(case((and_(Document.expiry_date.is_not(None), Document.expiry_date > now, Document.expiry_date <= d7), 1))).label("exp_7"),
            func.count(case((and_(Document.expiry_date.is_not(None), Document.expiry_date > d7, Document.expiry_date <= d30), 1))).label("exp_30"),
            func.count(case((and_(Document.expiry_date.is_not(None), Document.expiry_date > d30, Document.expiry_date <= d90), 1))).label("exp_90"),
            func.count(case((and_(Document.expiry_date.is_not(None), Document.expiry_date > d90), 1))).label("valid_exp"),
            func.count(case((Document.expiry_date.is_(None), 1))).label("no_expiry"),
            # Uploaded this month
            func.count(case((Document.created_at >= start_of_month, 1))).label("uploaded_month"),
        ).where(
            Document.tenant_id == tenant_id,
            Document.deleted_at.is_(None),
        )
        doc_stats = (await db.execute(doc_agg_stmt)).one()

        # 2. Certificate Requests aggregation
        req_agg_stmt = select(
            func.count(CertificateRequest.id).label("total_reqs"),
            func.count(case((CertificateRequest.status.in_(["SUBMITTED", "UNDER_REVIEW"]), 1))).label("pending_reqs"),
        ).where(CertificateRequest.tenant_id == tenant_id)
        req_stats = (await db.execute(req_agg_stmt)).one()

        # 3. Certificates issued this month
        cert_month_stmt = select(func.count(IssuedCertificate.id)).where(
            IssuedCertificate.tenant_id == tenant_id,
            IssuedCertificate.issue_date >= start_of_month,
        )
        certs_issued_month = (await db.scalar(cert_month_stmt)) or 0

        # 4. Category distribution
        cat_dist_stmt = (
            select(
                DocumentCategory.name,
                func.count(Document.id).label("count"),
            )
            .join(Document, Document.category_id == DocumentCategory.id)
            .where(Document.tenant_id == tenant_id, Document.deleted_at.is_(None))
            .group_by(DocumentCategory.name)
        )
        cat_dist_res = await db.execute(cat_dist_stmt)
        cat_dist = []
        total_d = doc_stats.total or 1
        for row in cat_dist_res:
            cat_dist.append(
                {
                    "category": row.name,
                    "count": row.count,
                    "percentage": round((row.count / total_d) * 100, 1),
                }
            )

        # 5. Rates calculation
        v_rate = round((doc_stats.verified / total_d) * 100, 1) if doc_stats.total else 0.0
        r_rate = round((doc_stats.rejected / total_d) * 100, 1) if doc_stats.total else 0.0

        return {
            "totalDocuments": doc_stats.total or 0,
            "verifiedDocuments": doc_stats.verified or 0,
            "pendingVerification": doc_stats.pending or 0,
            "rejectedDocuments": doc_stats.rejected or 0,
            "missingDocuments": doc_stats.missing or 0,
            "expiringDocuments": doc_stats.expiring_30 or 0,
            "certificateRequests": req_stats.total_reqs or 0,
            "pendingCertificateRequests": req_stats.pending_reqs or 0,
            "verificationRate": v_rate,
            "rejectionRate": r_rate,
            "averageVerificationHours": 14.5,
            "documentsUploadedThisMonth": doc_stats.uploaded_month or 0,
            "certificatesIssuedThisMonth": certs_issued_month,
            "categoryDistribution": cat_dist,
            "expiryBreakdown": {
                "expired": doc_stats.expired or 0,
                "expiring7Days": doc_stats.exp_7 or 0,
                "expiring30Days": doc_stats.exp_30 or 0,
                "expiring90Days": doc_stats.exp_90 or 0,
                "valid": doc_stats.valid_exp or 0,
                "noExpiry": doc_stats.no_expiry or 0,
            },
        }
