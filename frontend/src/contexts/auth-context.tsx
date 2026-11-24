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
import { PORTALS } from "@/lib/portals";
import { apiFetch, ApiClientError } from "@/lib/api-client";

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
    portal?: string;
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

export function resolveDemoPersona(raw: string): DemoPersona | null {
  if (!raw) return null;
  const id = raw.trim().toLowerCase();

  // 1. Direct match on email
  let found = DEMO_PERSONAS.find((p) => p.email.toLowerCase() === id);
  if (found) return found;

  // 2. Direct match on persona ID
  found = DEMO_PERSONAS.find((p) => p.id.toLowerCase() === id);
  if (found) return found;

  // 3. Direct match on role name
  found = DEMO_PERSONAS.find(
    (p) =>
      p.role.toLowerCase() === id ||
      ((id === "vice_principal" || id === "vice-principal") &&
        (p.role === "VICE_PRINCIPAL" || p.role === "PRINCIPAL")) ||
      (id === "admin" && p.role === "SUPER_ADMIN"),
  );
  if (found) return found;

  // 4. Portal configurations check (PORTALS mapping)
  const portal = Object.values(PORTALS).find(
    (p) =>
      p.demoEmail.toLowerCase() === id ||
      p.key.toLowerCase() === id ||
      p.canonicalRole.toLowerCase() === id ||
      p.shortTitle.toLowerCase() === id,
  );
  if (portal) {
    found = DEMO_PERSONAS.find((p) => p.id === portal.demoPersonaId);
    if (found) return found;
  }

  // 5. Student identifiers (roll number, email prefix, or student keywords)
  if (
    id.includes("2024-cse") ||
    id.includes("2024cse") ||
    id.includes("aarav") ||
    id === "student" ||
    id.startsWith("stu-") ||
    id.startsWith("roll-")
  ) {
    return DEMO_PERSONAS.find((p) => p.id === "user-student-01") || null;
  }

  // 6. Faculty identifiers (faculty ID, prof, or faculty keywords)
  if (
    id.includes("fac-cse") ||
    id.includes("fac_cse") ||
    id.includes("rajesh") ||
    id.includes("sharma") ||
    id === "faculty" ||
    id === "professor" ||
    id === "prof"
  ) {
    return DEMO_PERSONAS.find((p) => p.id === "user-faculty-01") || null;
  }

  // 7. Head of Department identifiers
  if (id.includes("hod") || id.includes("anand") || id.startsWith("hod-")) {
    return DEMO_PERSONAS.find((p) => p.id === "user-hod-cse-01") || null;
  }

  // 8. Vice Principal / Principal identifiers
  if (
    id.includes("vp") ||
    id.includes("vice") ||
    id.includes("principal") ||
    id.includes("swaminathan") ||
    id.includes("sundaram")
  ) {
    return DEMO_PERSONAS.find((p) => p.id === "user-vice-principal-01") || null;
  }

  // 9. Administrator / Registrar identifiers
  if (
    id.includes("registrar") ||
    id.includes("admin") ||
    id.includes("superadmin")
  ) {
    return DEMO_PERSONAS.find((p) => p.id === "user-super-admin-01") || null;
  }

  // 10. Secondary portals
  if (
    id.includes("account") ||
    id.includes("bursar") ||
    id.includes("finance")
  ) {
    return DEMO_PERSONAS.find((p) => p.id === "user-accounts-01") || null;
  }
  if (id.includes("placement") || id.includes("tpo")) {
    return DEMO_PERSONAS.find((p) => p.id === "user-placement-01") || null;
  }
  if (id.includes("warden") || id.includes("hostel")) {
    return DEMO_PERSONAS.find((p) => p.id === "user-warden-01") || null;
  }
  if (id.includes("transport") || id.includes("bus")) {
    return DEMO_PERSONAS.find((p) => p.id === "user-transport-01") || null;
  }
  if (id.includes("librar")) {
    return DEMO_PERSONAS.find((p) => p.id === "user-library-01") || null;
  }
  if (id.includes("secur")) {
    return DEMO_PERSONAS.find((p) => p.id === "user-security-01") || null;
  }
  if (id.includes("facilit") || id.includes("estate")) {
    return DEMO_PERSONAS.find((p) => p.id === "user-facility-01") || null;
  }

  return null;
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
            p.role === userRoleName ||
            p.id === response.data.id,
        );
        if (matched) {
          setActivePersona(matched);
        }
        setIsLoading(false);
        return;
      }
    } catch {
      // Backend not authenticated or offline. Fall through to local session recovery.
    }

    // Recover active persona from localStorage if available
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("campusos_active_persona");
      if (saved) {
        const found =
          resolveDemoPersona(saved) ||
          DEMO_PERSONAS.find(
            (p) =>
              p.id === saved ||
              p.role === saved ||
              p.email.toLowerCase() === saved.toLowerCase() ||
              (saved === "VICE_PRINCIPAL" && p.role === "PRINCIPAL") ||
              (saved === "PRINCIPAL" && p.role === "PRINCIPAL") ||
              (saved === "ADMIN" && p.role === "SUPER_ADMIN"),
          );
        if (found) {
          setActivePersona(found);
          setUser(personaToUser(found));
          setIsLoading(false);
          return;
        }
      }
    }

    setUser(null);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const switchPersona = useCallback((roleOrId: string) => {
    const target =
      resolveDemoPersona(roleOrId) ||
      DEMO_PERSONAS.find(
        (p) =>
          p.role === roleOrId ||
          p.id === roleOrId ||
          p.role.toLowerCase() === roleOrId.toLowerCase(),
      );
    if (target) {
      setActivePersona(target);
      setUser(personaToUser(target));
      if (typeof window !== "undefined") {
        localStorage.setItem("campusos_active_persona", target.id);
      }
    }
  }, []);

  const login = async (credentials: {
    email: string;
    password?: string;
    portal?: string;
  }): Promise<AuthenticatedUser | null> => {
    setIsLoading(true);
    const rawIdentifier = (credentials.email || "").trim();
    const normalizedIdentifier = rawIdentifier.toLowerCase();
    const enteredPassword = credentials.password?.trim() || "";

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
            p.role === userRoleName ||
            p.id === response.data.id,
        );
        if (matched) {
          setActivePersona(matched);
          if (typeof window !== "undefined") {
            localStorage.setItem("campusos_active_persona", matched.id);
          }
        } else if (typeof window !== "undefined") {
          localStorage.setItem(
            "campusos_active_persona",
            response.data.id || response.data.email,
          );
        }
        return response.data;
      }
    } catch (err: unknown) {
      // If backend explicitly rejected the credentials or portal, propagate that error directly!
      if (err instanceof ApiClientError) {
        throw new Error(err.message || "Invalid username or password.");
      }

      // Backend is offline / unreachable: Fallback to local institutional demo persona resolution
      const matchedPersona = resolveDemoPersona(normalizedIdentifier);

      if (matchedPersona) {
        // Enforce portal-role restriction in demo mode as well
        if (credentials.portal) {
          const portalKey = credentials.portal as keyof typeof PORTALS;
          const portalCfg = PORTALS[portalKey];
          if (portalCfg) {
            const isAuthorized =
              portalCfg.allowedRoles.includes(matchedPersona.role) ||
              (matchedPersona.role === "PRINCIPAL" &&
                portalCfg.allowedRoles.includes("VICE_PRINCIPAL"));
            if (!isAuthorized) {
              throw new Error(
                `Authentication succeeded, but your account is not authorized for the ${portalCfg.label}. Please select the appropriate portal.`,
              );
            }
          }
        }

        setActivePersona(matchedPersona);
        const authenticatedUser = personaToUser(matchedPersona);
        setUser(authenticatedUser);
        if (typeof window !== "undefined") {
          localStorage.setItem("campusos_active_persona", matchedPersona.id);
        }
        return authenticatedUser;
      }

      // If no demo persona match could be resolved, throw the error
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
