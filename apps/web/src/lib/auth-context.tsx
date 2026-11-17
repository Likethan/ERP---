"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import type { AuthenticatedUser } from "@campusos/types";
import { DEMO_PERSONAS } from "@/mocks/auth.mock";
import { DemoPersona } from "@/types/domain";
import { PORTALS } from "./portals";
import { apiFetch, ApiClientError } from "./api-client";

interface AuthContextValue {
  user: AuthenticatedUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  activePersona: DemoPersona;
  personas: DemoPersona[];
  hasPermission: (permissionCode: string) => boolean;
  hasRole: (roleName: string) => boolean;
  switchPersona: (roleOrId: string) => void;
  login: (credentials: {
    email: string;
    password?: string;
  }) => Promise<AuthenticatedUser | null>;
  logout: () => Promise<void>;
  clearSession: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function personaToUser(persona: DemoPersona): AuthenticatedUser {
  return {
    id: persona.id,
    email: persona.email,
    first_name: persona.name.split(" ")[0] || "User",
    last_name: persona.name.split(" ").slice(1).join(" ") || "",
    status: "ACTIVE",
    roles: [
      {
        id: `role-${persona.role.toLowerCase()}`,
        name: persona.role,
        display_name: persona.roleTitle,
        department_id: persona.department
          ? `dept-${persona.department.toLowerCase()}`
          : undefined,
      },
    ],
    permissions: persona.permissions,
    tenant: {
      id: "ten-vsb-01",
      code: "VSB-CAMPUS",
      name: "Vidyasagar State University of Engineering",
    },
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [activePersona, setActivePersona] = useState<DemoPersona>(
    DEMO_PERSONAS[0],
  );

  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const response = await apiFetch<AuthenticatedUser>("/api/v1/auth/me");
      if (response.success && response.data) {
        setUser(response.data);
        const userRoleName = response.data.roles?.[0]?.name;
        const matched = DEMO_PERSONAS.find(
          (p) =>
            p.email.toLowerCase() === response.data.email.toLowerCase() ||
            p.role === userRoleName,
        );
        if (matched) {
          setActivePersona(matched);
        }
      } else {
        setUser(null);
      }
    } catch {
      // Offline fallback: check whether an active persona session was previously saved
      if (typeof window !== "undefined") {
        const saved = localStorage.getItem("campusos_active_persona");
        if (saved) {
          const found = DEMO_PERSONAS.find(
            (p) => p.role === saved || p.id === saved,
          );
          if (found) {
            setActivePersona(found);
            setUser(personaToUser(found));
          } else {
            setUser(null);
          }
        } else {
          setUser(null);
        }
      } else {
        setUser(null);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const switchPersona = useCallback((roleOrId: string) => {
    const target = DEMO_PERSONAS.find(
      (p) =>
        p.role === roleOrId ||
        p.id === roleOrId ||
        p.role.toLowerCase() === roleOrId.toLowerCase(),
    );
    if (target) {
      setActivePersona(target);
      setUser(personaToUser(target));
      if (typeof window !== "undefined") {
        localStorage.setItem("campusos_active_persona", target.role);
      }
    }
  }, []);

  const login = async (credentials: {
    email: string;
    password?: string;
  }): Promise<AuthenticatedUser | null> => {
    setIsLoading(true);
    try {
      const response = await apiFetch<AuthenticatedUser>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(credentials),
      });

      if (response.success && response.data) {
        setUser(response.data);
        const userRoleName = response.data.roles?.[0]?.name;
        const matched = DEMO_PERSONAS.find(
          (p) =>
            p.email.toLowerCase() === response.data.email.toLowerCase() ||
            p.role === userRoleName,
        );
        if (matched) {
          setActivePersona(matched);
          if (typeof window !== "undefined") {
            localStorage.setItem("campusos_active_persona", matched.role);
          }
        }
        return response.data;
      }
    } catch (err: unknown) {
      if (err instanceof ApiClientError) {
        throw new Error(err.message || "Invalid username or password.");
      }

      // Offline development fallback verification
      const trimmedEmail = credentials.email.trim().toLowerCase();
      const personaMatch = DEMO_PERSONAS.find(
        (p) => p.email.toLowerCase() === trimmedEmail,
      );
      const portalMatch = Object.values(PORTALS).find(
        (p) => p.demoEmail.toLowerCase() === trimmedEmail,
      );

      const expectedPassword = portalMatch?.demoPassword || "Password123!";
      if (
        credentials.password &&
        (credentials.password === expectedPassword ||
          credentials.password === "CampusOS2026!" ||
          credentials.password === "SuperSecret123!" ||
          credentials.password === "StudentSecret123!" ||
          credentials.password === "FacultySecret123!" ||
          credentials.password === "HodSecret123!" ||
          credentials.password === "ExecutiveSecret123!")
      ) {
        const targetPersona =
          personaMatch ||
          (portalMatch
            ? DEMO_PERSONAS.find((p) => p.id === portalMatch.demoPersonaId)
            : null) ||
          DEMO_PERSONAS[0];
        setActivePersona(targetPersona);
        const authenticatedUser = personaToUser(targetPersona);
        setUser(authenticatedUser);
        if (typeof window !== "undefined") {
          localStorage.setItem("campusos_active_persona", targetPersona.role);
        }
        return authenticatedUser;
      }

      throw new Error("Invalid username or password.");
    } finally {
      setIsLoading(false);
    }
    return null;
  };

  const clearSession = useCallback(async () => {
    try {
      await apiFetch<{ message: string }>("/api/v1/auth/logout", {
        method: "POST",
      });
    } catch {
      // Ignore network errors
    } finally {
      setUser(null);
      if (typeof window !== "undefined") {
        localStorage.removeItem("campusos_active_persona");
      }
    }
  }, []);

  const logout = async () => {
    await clearSession();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  };

  const hasPermission = useCallback(
    (permissionCode: string): boolean => {
      if (!user) return false;
      if (
        user.roles?.some((r) => r.name === "SUPER_ADMIN" || r.name === "ADMIN")
      )
        return true;
      if (user.permissions?.includes("*")) return true;
      return user.permissions?.includes(permissionCode) ?? false;
    },
    [user],
  );

  const hasRole = useCallback(
    (roleName: string): boolean => {
      if (!user) return false;
      return user.roles?.some((r) => r.name === roleName) ?? false;
    },
    [user],
  );

  const value: AuthContextValue = {
    user,
    isLoading,
    isAuthenticated: Boolean(user),
    activePersona,
    personas: DEMO_PERSONAS,
    hasPermission,
    hasRole,
    switchPersona,
    login,
    logout,
    clearSession,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
