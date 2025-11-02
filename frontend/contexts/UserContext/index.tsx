"use client";
import { createContext, useContext, useState, ReactNode, useEffect } from "react";
import { getCurrentUser } from "@/lib/auth";

type User = { username: string } | null;
type UserContextType = { user: User; setUser: (u: User) => void };

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User>(null);
  useEffect(() => {
    async function fetchUser() {
      const u = await getCurrentUser();
      setUser(u);
    }
    fetchUser();
  }, []);
  return (
    <UserContext.Provider value={{ user, setUser }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used within UserProvider");
  return ctx;
}
