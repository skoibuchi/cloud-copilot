"use client";

import Link from "next/link";
import LogoutButton from "@/components/LogoutButton";
import { useUser } from "@/contexts/UserContext";

export default function Sidebar() {
  const { user } = useUser();

  return (
    <aside className="w-60 bg-gray-800 text-white p-4 flex flex-col space-y-2">
      {user ? (
        <>
          <div className="mb-4">Hello, {user.username}</div>
          <Link href="/chat" className="hover:bg-gray-700 p-2 rounded cursor-pointer">
            Chat
          </Link>
          <Link href="/cloud" className="hover:bg-gray-700 p-2 rounded cursor-pointer">
            Cloud Settings
          </Link>
          <LogoutButton />
        </>
      ) : (
        <Link href="/login" className="hover:bg-gray-700 p-2 rounded cursor-pointer">
          Login
        </Link>
      )}
    </aside>
  );
}
