'use client';

import { useState, useEffect, useCallback } from 'react';
import { getToken } from '@/lib/api';

interface UseFetchOptions<T> {
    onSuccess?: (data: T) => void;
    onError?: (error: Error) => void;
    immediate?: boolean;
}

interface UseFetchResult<T> {
    data: T | null;
    isLoading: boolean;
    error: Error | null;
    refetch: () => Promise<void>;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Custom hook for client-side data fetching with automatic auth header injection
 */
export function useFetch<T>(
    endpoint: string,
    options: UseFetchOptions<T> = {}
): UseFetchResult<T> {
    const { onSuccess, onError, immediate = true } = options;
    const [data, setData] = useState<T | null>(null);
    const [isLoading, setIsLoading] = useState(immediate);
    const [error, setError] = useState<Error | null>(null);

    const fetchData = useCallback(async () => {
        setIsLoading(true);
        setError(null);

        try {
            const token = getToken();
            const headers: HeadersInit = {
                'Content-Type': 'application/json',
            };

            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'GET',
                headers,
            });

            if (!response.ok) {
                let errorMessage = 'An error occurred';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch {
                    errorMessage = response.statusText || errorMessage;
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            setData(result);
            onSuccess?.(result);
        } catch (err) {
            const error = err instanceof Error ? err : new Error('Unknown error');
            setError(error);
            onError?.(error);
        } finally {
            setIsLoading(false);
        }
    }, [endpoint, onSuccess, onError]);

    useEffect(() => {
        if (immediate) {
            fetchData();
        }
    }, [immediate, fetchData]);

    return {
        data,
        isLoading,
        error,
        refetch: fetchData,
    };
}

/**
 * Hook for mutation operations (POST, PUT, DELETE)
 */
interface UseMutationOptions<T, R> {
    onSuccess?: (data: R) => void;
    onError?: (error: Error) => void;
}

interface UseMutationResult<T, R> {
    mutate: (data: T) => Promise<R | null>;
    isLoading: boolean;
    error: Error | null;
    reset: () => void;
}

export function useMutation<T, R>(
    endpoint: string,
    method: 'POST' | 'PUT' | 'PATCH' | 'DELETE' = 'POST',
    options: UseMutationOptions<T, R> = {}
): UseMutationResult<T, R> {
    const { onSuccess, onError } = options;
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const mutate = useCallback(
        async (data: T): Promise<R | null> => {
            setIsLoading(true);
            setError(null);

            try {
                const token = getToken();
                const headers: HeadersInit = {
                    'Content-Type': 'application/json',
                };

                if (token) {
                    headers['Authorization'] = `Bearer ${token}`;
                }

                const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                    method,
                    headers,
                    body: JSON.stringify(data),
                });

                if (!response.ok) {
                    let errorMessage = 'An error occurred';
                    try {
                        const errorData = await response.json();
                        errorMessage = errorData.detail || errorMessage;
                    } catch {
                        errorMessage = response.statusText || errorMessage;
                    }
                    throw new Error(errorMessage);
                }

                // Handle empty responses
                if (response.status === 204) {
                    onSuccess?.({} as R);
                    return {} as R;
                }

                const result = await response.json();
                onSuccess?.(result);
                return result;
            } catch (err) {
                const error = err instanceof Error ? err : new Error('Unknown error');
                setError(error);
                onError?.(error);
                return null;
            } finally {
                setIsLoading(false);
            }
        },
        [endpoint, method, onSuccess, onError]
    );

    const reset = useCallback(() => {
        setError(null);
    }, []);

    return {
        mutate,
        isLoading,
        error,
        reset,
    };
}
