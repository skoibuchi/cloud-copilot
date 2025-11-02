import { getCurrentUser } from "@/lib/auth";
import LoginPage from "./login/page";
import ChatPage from "@/app/chat";

export default async function HomePage() {
  const user = await getCurrentUser();

  if (!user) {
    return <LoginPage />
  }

  return <ChatPage userId={user.username} />;
}
