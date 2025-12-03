/**
 * TypeScript interfaces for API types
 */

export interface User {
    id: string;
    email: string;
    full_name: string;
    preferred_time: string;
    // NOTE: timezone field disabled - all users use UTC
    // timezone: string;
    is_active: boolean;
    interests: InterestSummary[];
    created_at: string;
    updated_at: string;
}

export interface InterestSummary {
    id: string;
    slug: string;
    name: string;
}

export interface Interest {
    id: string;
    name: string;
    slug: string;
    description: string | null;
    is_active: boolean;
    display_order: number;
    created_at: string;
}

export interface InterestListResponse {
    interests: Interest[];
    total: number;
}

export interface DigestSummary {
    id: string;
    digest_date: string;
    summary: string | null;
    interests_included: string[];
    word_count: number | null;
    status: string;
    created_at: string;
}

export interface HeadlineInfo {
    title: string;
    source: string;
    url: string;
    published_at: string;
    category: string;
}

export interface DigestDetail {
    id: string;
    user_id: string;
    digest_date: string;
    content: string;
    summary: string | null;
    headlines_used: HeadlineInfo[];
    interests_included: string[];
    word_count: number | null;
    status: string;
    created_at: string;
}

export interface DigestListResponse {
    digests: DigestSummary[];
    total: number;
    page: number;
    per_page: number;
    has_next: boolean;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    expires_in: number;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface RegisterRequest {
    email: string;
    password: string;
    full_name: string;
    preferred_time?: string;
    // NOTE: timezone field disabled - all users use UTC
    // timezone?: string;
}

export interface UserPreferencesUpdate {
    preferred_time?: string;
    // NOTE: timezone field disabled - all users use UTC
    // timezone?: string;
}

export interface UserInterestUpdate {
    interest_slugs: string[];
}

export interface ApiError {
    detail: string;
    status?: number;
}
