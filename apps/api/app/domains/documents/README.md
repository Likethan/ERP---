# Documents Domain (`app/domains/documents`)

## Purpose

Governs digital document archival, student identity verification files, and automated certificate issuance (Bonafide, Transfer Certificate, Transcripts).

## Key Entities

- `DocumentCategory`
- `StudentDocument` (e.g., 10th/12th grade marksheets, identity proof)
- `CertificateTemplate`
- `IssuedCertificate`
- `CredentialVerificationLog`

## Boundaries & Constraints

- Physical binary files reside in S3 / MinIO storage; only signed URIs, cryptographic SHA-256 hashes, and metadata are maintained in the database.
- Read/download access requires strict permission enforcement and actor validation.
