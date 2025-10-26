"use client";

import { useState, useRef, useEffect } from "react";

type Message = { role: "user" | "ai"; content: string };

type CloudResource = {
  provider: string;
  vms?: string[];
  buckets?: string[];
  [key: string]: any;
};

export default function Home() {
  const [userId, setUserId] = useState("default_user");  // set default userId for dev
  const [input, setInput] = useState("");
  const [chatLog, setChatLog] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState<FileList | null>(null);
  const [cloudResources, setCloudResources] = useState<CloudResource[]>([]);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auto scroll
  useEffect(() => {
    chatContainerRef.current?.scrollTo({
      top: chatContainerRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [chatLog]);

  // Chat Submit
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
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        body: formData,
      });

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

  // 最新構成取得ボタン
const fetchCloudResources = async () => {
  try {
    const API_URL = process.env.NEXT_PUBLIC_API_URL;
    const res = await fetch(`${API_URL}/cloud-resources`);
    const data = await res.json();

    const resourcesArray: CloudResource[] = Object.entries(data).map(
      ([provider, info]) => ({
        provider,
        vms: (info as any).vms ?? [],
        buckets: (info as any).buckets ?? [],
        ...(info as any),
      })
    );
    setCloudResources(resourcesArray);
  } catch (err) {
    console.error("Error fetching cloud resources:", err);
  }
};

  // Cloud environment info tree status
  const [collapsedNodes, setCollapsedNodes] = useState<Set<string>>(new Set());

  const toggleCollapse = (path: string) => {
    setCollapsedNodes((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(path)) newSet.delete(path);
      else newSet.add(path);
      return newSet;
    });
  };

  const renderTree = (resource: any, path: string = "") => {
    return Object.entries(resource).map(([key, value]) => {
      const currentPath = path ? `${path}.${key}` : key;
      if (Array.isArray(value)) {
        return (
          <li key={currentPath}>
            <span
              className="cursor-pointer font-semibold"
              onClick={() => toggleCollapse(currentPath)}
            >
              {collapsedNodes.has(currentPath) ? "▶ " : "▼ "} {key} ({value.length})
            </span>
            {!collapsedNodes.has(currentPath) && (
              <ul className="pl-5">
                {value.map((item, idx) => (
                  <li key={`${currentPath}-${idx}`}>{item}</li>
                ))}
              </ul>
            )}
          </li>
        );
      } else if (typeof value === "object" && value !== null) {
        return (
          <li key={currentPath}>
            <span
              className="cursor-pointer font-semibold"
              onClick={() => toggleCollapse(currentPath)}
            >
              {collapsedNodes.has(currentPath) ? "▶ " : "▼ "} {key}
            </span>
            {!collapsedNodes.has(currentPath) && (
              <ul className="pl-5">{renderTree(value, currentPath)}</ul>
            )}
          </li>
        );
      } else {
        return (
          <li key={currentPath}>
            <strong>{key}:</strong> {String(value)}
          </li>
        );
      }
    });
  };

  return (
    <div className="p-4 max-w-full mx-auto flex gap-4 h-screen">
      {/* Left: Cloud Info */}
      <div className="w-1/3 border rounded p-4 overflow-y-auto">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold">Cloud Environment Info</h2>
          <button
            className="text-sm bg-gray-200 hover:bg-gray-300 rounded px-2 py-1"
            onClick={fetchCloudResources}
          >
            Refresh
          </button>
        </div>
        {cloudResources.length === 0 ? (
          <p className="text-gray-500">No information</p>
        ) : (
          <ul className="list-none pl-0">
            {cloudResources.map((res, idx) => (
              <li key={idx}>
                <span
                  className="cursor-pointer font-bold"
                  onClick={() => toggleCollapse(res.provider)}
                >
                  {collapsedNodes.has(res.provider) ? "▶ " : "▼ "} {res.provider}
                </span>
                {!collapsedNodes.has(res.provider) && (
                  <ul className="pl-5">{renderTree(res, res.provider)}</ul>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Right: Chat UI */}
      <div className="w-2/3 flex flex-col">
        <h2 className="text-xl font-bold mb-2">Chat</h2>
        <div
          ref={chatContainerRef}
          className="border rounded p-4 h-full overflow-y-auto flex flex-col gap-2 mb-2"
        >
          {chatLog.map((msg, idx) => (
            <div
              key={idx}
              className={`${msg.role === "user" ? "text-right" : "text-left"}`}
            >
              <strong>{msg.role === "user" ? "You" : "AI"}:</strong>{" "}
              {msg.content}
            </div>
          ))}
          {loading && (
            <div className="italic text-gray-500">AI is thinking...</div>
          )}
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
            {files && files.length > 0
              ? `${files.length} files selected`
              : "Select a file"}
            <input
              type="file"
              multiple
              className="hidden"
              onChange={(e) => setFiles(e.target.files)}
            />
          </label>

          <button
            className="bg-blue-500 text-white rounded px-4 py-2 hover:bg-blue-600"
            onClick={handleSend}
            disabled={loading}
          >
            Submit
          </button>
        </div>
      </div>
    </div>
  );
}
