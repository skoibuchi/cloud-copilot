'use server'

import { cookies } from "next/headers";
import jwt from "jsonwebtoken";

export async function getCurrentUser() {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;

  if (!token) return null;

  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET!);
    return { username: (payload as any).sub }
  } catch {
    return null;
  }
}

export async function logoutCurrentUser() {
  const response = (await cookies()).delete('token')
}

export async function getToken() {
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;
  return token
}