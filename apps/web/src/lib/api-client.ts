import type {
  ApiResponse,
  ApiErrorResponse,
  PaginatedResponse,
} from "@campusos/types";

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

const inFlightRequests = new Map<string, Promise<unknown>>();

/**
 * Type-safe HTTP client for CampusOS Backend API with in-flight GET request deduplication.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<ApiResponse<T>> {
  const method = (options.method || "GET").toUpperCase();
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

  // Deduplicate concurrent identical in-flight GET requests
  if (method === "GET" && !options.body) {
    const existing = inFlightRequests.get(url);
    if (existing) {
      return existing as Promise<ApiResponse<T>>;
    }
  }

  const execute = async (): Promise<ApiResponse<T>> => {
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
  };

  if (method === "GET" && !options.body) {
    const promise = execute().finally(() => {
      inFlightRequests.delete(url);
    });
    inFlightRequests.set(url, promise);
    return promise;
  }

  return execute();
}

/**
 * Type-safe HTTP client for paginated endpoints with in-flight GET request deduplication.
 */
export async function apiFetchPaginated<T>(
  path: string,
  options: RequestInit = {},
): Promise<PaginatedResponse<T>> {
  const method = (options.method || "GET").toUpperCase();
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

  // Deduplicate concurrent identical in-flight GET requests
  if (method === "GET" && !options.body) {
    const existing = inFlightRequests.get(url);
    if (existing) {
      return existing as Promise<PaginatedResponse<T>>;
    }
  }

  const execute = async (): Promise<PaginatedResponse<T>> => {
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
  };

  if (method === "GET" && !options.body) {
    const promise = execute().finally(() => {
      inFlightRequests.delete(url);
    });
    inFlightRequests.set(url, promise);
    return promise;
  }

  return execute();
}
