"use client";

import { useState } from "react";
import ChatBox from "@/components/ChatBox";
import CloudResources from "@/components/CloudResources";
import { Message, CloudResource } from "@/types";


export default function Home() {
  const [userId, setUserId] = useState("default_user"); // 開発用デフォルト
  const [chatLog, setChatLog] = useState<Message[]>([]);
  const [cloudResources, setCloudResources] = useState<CloudResource[]>([]);

  return (
    <div className="p-4 max-w-full mx-auto flex gap-4 h-screen">
      {/* Left: Cloud Info */}
      <div className="w-1/3 border rounded p-4 overflow-y-auto">
        <CloudResources
          cloudResources={cloudResources}
          setCloudResources={setCloudResources}
        />
      </div>

      {/* Right: Chat UI */}
      <div className="w-2/3 flex flex-col">
        <ChatBox
          userId={userId}
          chatLog={chatLog}
          setChatLog={setChatLog}
          setCloudResources={setCloudResources}
        />
      </div>
    </div>
  );
}
