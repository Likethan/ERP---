import type {
  ApiResponse,
  ApiErrorResponse,
  PaginatedResponse,
} from "@campusos/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export class ApiClientError extends Error {
  public readonly isRateLimited: boolean;
  public readonly retryAfterSeconds?: number;
  public readonly rateLimitLimit?: number;
  public readonly rateLimitRemaining?: number;
  public readonly rateLimitReset?: number;

  constructor(
    public readonly statusCode: number,
    public readonly errorResponse: ApiErrorResponse,
    headers?: Headers,
  ) {
    const isThrottled = statusCode === 429;
    const retryAfter = headers?.get("Retry-After")
      ? parseInt(headers.get("Retry-After")!, 10)
      : undefined;

    const baseMessage =
      errorResponse.error.message ||
      (isThrottled
        ? `Rate limit exceeded. Please wait ${retryAfter ?? 60} seconds before retrying.`
        : `API Request failed with status ${statusCode}`);

    super(baseMessage);
    this.name = "ApiClientError";
    this.isRateLimited = isThrottled;
    this.retryAfterSeconds = retryAfter;
    this.rateLimitLimit = headers?.get("X-RateLimit-Limit")
      ? parseInt(headers.get("X-RateLimit-Limit")!, 10)
      : undefined;
    this.rateLimitRemaining = headers?.get("X-RateLimit-Remaining")
      ? parseInt(headers.get("X-RateLimit-Remaining")!, 10)
      : undefined;
    this.rateLimitReset = headers?.get("X-RateLimit-Reset")
      ? parseInt(headers.get("X-RateLimit-Reset")!, 10)
      : undefined;
  }
}

const inFlightRequests = new Map<string, Promise<unknown>>();

function getSignalWithTimeout(
  customSignal?: AbortSignal | null,
  timeoutMs = 3500,
): AbortSignal | undefined {
  if (customSignal) return customSignal;
  if (
    typeof AbortSignal !== "undefined" &&
    typeof AbortSignal.timeout === "function"
  ) {
    return AbortSignal.timeout(timeoutMs);
  }
  return undefined;
}

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
      signal: getSignalWithTimeout(options.signal),
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
      throw new ApiClientError(response.status, errorData, response.headers);
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
      signal: getSignalWithTimeout(options.signal),
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
      throw new ApiClientError(response.status, errorData, response.headers);
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
