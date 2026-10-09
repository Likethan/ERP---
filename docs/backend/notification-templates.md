# Message Templates and Rendering Engine

## Template Overview

CampusOS message templates (`NotificationTemplate` and `NotificationTemplateVersion`) provide reusable, multi-lingual, channel-specific message definitions with strict version control and safe token interpolation.

## Version Lifecycle

Templates follow an immutable versioning lifecycle:

```text
DRAFT  →  publish  →  ACTIVE  →  deprecate  →  DEPRECATED / INACTIVE
```

1. **Immutable Publishing**: Active versions cannot change silently. Modifying template content increments `version` (e.g. v1 -> v2) and creates a new immutable `NotificationTemplateVersion` record with audit history.
2. **Channel Specialization**: Each template belongs to a channel (`IN_APP`, `EMAIL`, `SMS`, `PUSH`).
3. **Locale Support**: Templates support locale variants (`en`, `hi`, `ta`, etc.). If a requested user locale is not published, the engine automatically falls back to `en`.

## Safe Rendering Engine

`NotificationTemplateService` provides deterministic, injection-safe template rendering without dynamic code execution:

- **Safe Interpolation**: Uses explicit `{{variable}}` regex interpolation.
- **No Code Execution**: Arbitrary Python expressions, JavaScript, SQL, or shell commands are forbidden and impossible to execute.
- **HTML Escaping**: When rendering HTML email bodies (`render_html`), all user-supplied variables are escaped using standard HTML sanitization (`html.escape`) to prevent cross-site scripting (XSS).
- **Missing Variable Validation**: If a variable marked as `"required": True` in the version's `variable_schema_json` is missing from the payload, rendering throws a `ValidationException`.
- **Bounded Template Size**: Templates are capped at 64KB (`MAX_TEMPLATE_SIZE_BYTES = 65536`) to prevent memory exhaustion and denial-of-service attacks.

## Variable Schema Example

```json
{
  "student_name": {
    "type": "string",
    "required": true,
    "description": "Full name of the student"
  },
  "course_code": {
    "type": "string",
    "required": true,
    "description": "Course identifier"
  },
  "attendance_percentage": {
    "type": "number",
    "required": true,
    "description": "Current attendance percentage"
  }
}
```

## Template Preview API

Authorized administrators can preview templates before publishing using sample contexts:

```http
POST /api/v1/admin/notification-templates/{template_id}/preview
Content-Type: application/json

{
  "locale": "en",
  "context": {
    "student_name": "Dev Sharma",
    "course_code": "CS101",
    "attendance_percentage": 72.5
  }
}
```

Response includes rendered subject, body text, HTML preview, missing variable analysis, and validation status without creating delivery records.
