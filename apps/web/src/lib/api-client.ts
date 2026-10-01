import type { ApiResponse, ApiErrorResponse, PaginatedResponse } from "@campusos/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiClientError extends Error {
  constructor(
    public readonly statusCode: number,
    public readonly errorResponse: ApiErrorResponse,
  ) {
    super(
      errorResponse.error.message ||
        `API Request failed with status ${statusCode}`,
    );
    this.name = "ApiClientError";
  }
}

/**
 * Type-safe HTTP client for CampusOS Backend API
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    let errorData: ApiErrorResponse;
    try {
      errorData = await response.json();
    } catch {
      errorData = {
        success: false,
        error: {
          code: "HTTP_ERROR",
          message:
            response.statusText ||
            `Request failed with status ${response.status}`,
          timestamp: new Date().toISOString(),
        },
      };
    }
    throw new ApiClientError(response.status, errorData);
  }

  return response.json();
}

/**
 * Type-safe HTTP client for paginated endpoints
 */
export async function apiFetchPaginated<T>(
  path: string,
  options: RequestInit = {},
): Promise<PaginatedResponse<T>> {
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    let errorData: ApiErrorResponse;
    try {
      errorData = await response.json();
    } catch {
      errorData = {
        success: false,
        error: {
          code: "HTTP_ERROR",
          message:
            response.statusText ||
            `Request failed with status ${response.status}`,
          timestamp: new Date().toISOString(),
        },
      };
    }
    throw new ApiClientError(response.status, errorData);
  }

  return response.json();
}

