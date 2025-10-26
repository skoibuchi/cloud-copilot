"use client";

import { useState, useRef, useEffect } from "react";
import { Message, CloudResource } from "@/types";

interface Props {
  userId: string;
  chatLog: Message[];
  setChatLog: React.Dispatch<React.SetStateAction<Message[]>>;
  setCloudResources: React.Dispatch<React.SetStateAction<CloudResource[]>>;
}

export default function ChatBox({ userId, chatLog, setChatLog, setCloudResources }: Props) {
  const [input, setInput] = useState("");
  const [files, setFiles] = useState<FileList | null>(null);
  const [loading, setLoading] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auto scroll
  useEffect(() => {
    chatContainerRef.current?.scrollTo({
      top: chatContainerRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [chatLog]);

  const handleSend = async () => {
    if (!input.trim() && !files) return;

    if (input.trim()) {
      setChatLog((prev) => [...prev, { role: "user", content: input }]);
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("user_id", userId);
      formData.append("query", input);
      if (files) Array.from(files).forEach((file) => formData.append("files", file));

      const API_URL = process.env.NEXT_PUBLIC_API_URL;
      const res = await fetch(`${API_URL}/chat`, { method: "POST", body: formData });
      const data = await res.json();

      setChatLog((prev) => [...prev, { role: "ai", content: data.reply }]);

      if (data.cloudResources) {
        const resourcesArray: CloudResource[] = Object.entries(data.cloudResources).map(
          ([provider, info]) => ({
            provider,
            vms: (info as any).vms ?? [],
            buckets: (info as any).buckets ?? [],
            ...(info as any),
          })
        );
        setCloudResources(resourcesArray);
      }
    } catch (err) {
      setChatLog((prev) => [...prev, { role: "ai", content: `Error: ${err}` }]);
    } finally {
      setLoading(false);
      setInput("");
      setFiles(null);
    }
  };

  return (
    <>
      <h2 className="text-xl font-bold mb-2">Chat</h2>
      <div
        ref={chatContainerRef}
        className="border rounded p-4 h-full overflow-y-auto flex flex-col gap-2 mb-2"
      >
        {chatLog.map((msg, idx) => (
          <div key={idx} className={`${msg.role === "user" ? "text-right" : "text-left"}`}>
            <strong>{msg.role === "user" ? "You" : "AI"}:</strong> {msg.content}
          </div>
        ))}
        {loading && <div className="italic text-gray-500">AI is thinking...</div>}
      </div>

      <div className="flex flex-col gap-2 mt-auto">
        <input
          type="text"
          className="border rounded p-2 flex-1"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Example: Stop vm-test1"
        />

        <label className="border border-gray-300 rounded p-2 bg-gray-50 cursor-pointer hover:bg-gray-100 text-center">
          {files && files.length > 0 ? `${files.length} files selected` : "Select a file"}
          <input type="file" multiple className="hidden" onChange={(e) => setFiles(e.target.files)} />
        </label>

        <button
          className="bg-blue-500 text-white rounded px-4 py-2 hover:bg-blue-600"
          onClick={handleSend}
          disabled={loading}
        >
          Submit
        </button>
      </div>
    </>
  );
}
