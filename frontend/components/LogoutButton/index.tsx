'use client'
import { useRouter } from "next/navigation";
import { useUser } from "@/contexts/UserContext";

export default function LogoutButton() {
  const router = useRouter();
  const { setUser } = useUser();

  const handleLogout = async () => {
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
    setUser(null);
    router.push("/login");
  };

  return (
    <button
      onClick={handleLogout}
      className="hover:bg-gray-700 p-2 rounded w-full text-left cursor-pointer"
    >
      Logout
    </button>
  );
}
