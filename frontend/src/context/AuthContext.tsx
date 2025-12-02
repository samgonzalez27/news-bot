'use client';

import React, {
    createContext,
    useContext,
    useState,
    useEffect,
    useCallback,
    type ReactNode,
} from 'react';
import {
    getToken,
    setToken,
    removeToken,
    login as apiLogin,
    register as apiRegister,
    getCurrentUser,
    ApiRequestError,
} from '@/lib/api';
import type { User, LoginRequest, RegisterRequest } from '@/lib/types';

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (credentials: LoginRequest) => Promise<void>;
    register: (data: RegisterRequest) => Promise<void>;
    logout: () => void;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
    children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const isAuthenticated = user !== null;

    // Initialize auth state from stored token
    useEffect(() => {
        const initAuth = async () => {
            const token = getToken();
            if (token) {
                try {
                    const userData = await getCurrentUser();
                    setUser(userData);
                } catch {
                    // Token invalid or expired
                    removeToken();
                    setUser(null);
                }
            }
            setIsLoading(false);
        };

        initAuth();
    }, []);

    const login = useCallback(async (credentials: LoginRequest) => {
        const response = await apiLogin(credentials);
        setToken(response.access_token);
        const userData = await getCurrentUser();
        setUser(userData);
    }, []);

    const register = useCallback(async (data: RegisterRequest): Promise<void> => {
        console.log('[Auth] register: starting registration');

        try {
            await apiRegister(data);
            console.log('[Auth] register: registration successful');
            // Registration successful - caller will handle redirect to login
        } catch (regError) {
            console.error('[Auth] register: registration failed', regError);

            // Convert ApiRequestError to a more user-friendly message
            if (regError instanceof ApiRequestError) {
                throw new Error(regError.detail);
            }
            // Re-throw with original error if it's already an Error
            if (regError instanceof Error) {
                throw regError;
            }
            // Fallback for unknown error types
            throw new Error('Registration failed. Please try again.');
        }
    }, []);

    const logout = useCallback(() => {
        removeToken();
        setUser(null);
        if (typeof window !== 'undefined') {
            window.location.href = '/';
        }
    }, []);

    const refreshUser = useCallback(async () => {
        try {
            const userData = await getCurrentUser();
            setUser(userData);
        } catch {
            // If refresh fails, log out
            logout();
        }
    }, [logout]);

    const value: AuthContextType = {
        user,
        isAuthenticated,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

/**
 * Hook to require authentication - redirects to login if not authenticated
 */
export function useRequireAuth(): AuthContextType {
    const auth = useAuth();

    useEffect(() => {
        if (!auth.isLoading && !auth.isAuthenticated) {
            window.location.href = '/login';
        }
    }, [auth.isLoading, auth.isAuthenticated]);

    return auth;
}
