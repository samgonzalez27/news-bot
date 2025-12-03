/**
 * API Client for NewsDigest backend
 * Handles all HTTP requests with automatic token injection and error handling
 */

import type {
    User,
    TokenResponse,
    LoginRequest,
    RegisterRequest,
    Interest,
    InterestListResponse,
    DigestDetail,
    DigestListResponse,
    UserPreferencesUpdate,
    UserInterestUpdate,
    ApiError,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';
const TOKEN_KEY = 'newsdigest_token';

/**
 * Get stored auth token
 */
export function getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(TOKEN_KEY);
}

/**
 * Store auth token
 */
export function setToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Remove auth token
 */
export function removeToken(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(TOKEN_KEY);
}

/**
 * Check if token exists
 */
export function hasToken(): boolean {
    return getToken() !== null;
}

/**
 * Custom API error class
 */
export class ApiRequestError extends Error {
    status: number;
    detail: string;

    constructor(status: number, detail: string) {
        super(detail);
        this.name = 'ApiRequestError';
        this.status = status;
        this.detail = detail;
    }
}

/**
 * Base fetch wrapper with auth header injection and error handling
 */
async function apiFetch<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const url = `${API_BASE_URL}${API_PREFIX}${endpoint}`;
    const token = getToken();

    const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (token) {
        (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
        ...options,
        headers,
    });

    // Handle non-OK responses
    if (!response.ok) {
        let errorDetail = 'An error occurred';

        try {
            const errorData: ApiError = await response.json();
            errorDetail = errorData.detail || errorDetail;
        } catch {
            errorDetail = response.statusText || errorDetail;
        }

        // For 401, just clear the token - let the caller handle redirects
        // This avoids redirecting from public pages (e.g., landing page)
        // Protected pages use useRequireAuth which handles redirects properly
        if (response.status === 401) {
            removeToken();
        }

        throw new ApiRequestError(response.status, errorDetail);
    }

    // Handle empty responses
    if (response.status === 204) {
        return {} as T;
    }

    return response.json();
}

// =============================================================================
// Auth API
// =============================================================================

/**
 * Login with email and password
 */
export async function login(credentials: LoginRequest): Promise<TokenResponse> {
    return apiFetch<TokenResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
    });
}

/**
 * Register a new user
 */
export async function register(data: RegisterRequest): Promise<User> {
    console.log('[API] register: starting registration for', data.email);
    try {
        const result = await apiFetch<User>('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data),
        });
        console.log('[API] register: success for', data.email);
        return result;
    } catch (error) {
        console.error('[API] register: failed for', data.email, error);
        throw error;
    }
}

/**
 * Get current user profile
 */
export async function getCurrentUser(): Promise<User> {
    return apiFetch<User>('/users/me');
}

// =============================================================================
// User API
// =============================================================================

/**
 * Update user preferences
 */
export async function updateUserPreferences(
    data: UserPreferencesUpdate
): Promise<User> {
    return apiFetch<User>('/users/me/preferences', {
        method: 'PATCH',
        body: JSON.stringify(data),
    });
}

/**
 * Update user interests
 */
export async function updateUserInterests(
    data: UserInterestUpdate
): Promise<User> {
    return apiFetch<User>('/users/me/interests', {
        method: 'PUT',
        body: JSON.stringify(data),
    });
}

// =============================================================================
// Interests API
// =============================================================================

/**
 * Get all available interests
 */
export async function getInterests(): Promise<InterestListResponse> {
    return apiFetch<InterestListResponse>('/interests');
}

/**
 * Get a single interest by slug
 */
export async function getInterest(slug: string): Promise<Interest> {
    return apiFetch<Interest>(`/interests/${slug}`);
}

// =============================================================================
// Digest API
// =============================================================================

/**
 * Get list of user's digests
 */
export async function getDigests(
    page: number = 1,
    perPage: number = 10
): Promise<DigestListResponse> {
    return apiFetch<DigestListResponse>(
        `/digests?page=${page}&per_page=${perPage}`
    );
}

/**
 * Get a specific digest by ID
 */
export async function getDigest(id: string): Promise<DigestDetail> {
    return apiFetch<DigestDetail>(`/digests/${id}`);
}

/**
 * Get the latest digest for current user
 */
export async function getLatestDigest(): Promise<DigestDetail | null> {
    try {
        const response = await getDigests(1, 1);
        if (response.digests.length > 0) {
            return getDigest(response.digests[0].id);
        }
        return null;
    } catch {
        return null;
    }
}

/**
 * Generate a new digest
 */
export async function generateDigest(digestDate?: string): Promise<DigestDetail> {
    const body = digestDate ? { digest_date: digestDate } : {};
    return apiFetch<DigestDetail>('/digests/generate', {
        method: 'POST',
        body: JSON.stringify(body),
    });
}

// =============================================================================
// Health API
// =============================================================================

/**
 * Check API health
 */
export async function checkHealth(): Promise<{ status: string }> {
    // Health check uses root path, not API prefix
    const url = `${API_BASE_URL}/health`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new ApiRequestError(response.status, 'Health check failed');
    }
    return response.json();
}
