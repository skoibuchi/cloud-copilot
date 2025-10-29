"use client";

import { useState } from "react";
import { CloudResource } from "@/types";

interface Props {
  cloudResources: CloudResource[];
  setCloudResources: React.Dispatch<React.SetStateAction<CloudResource[]>>;
}

export default function CloudResources({ cloudResources, setCloudResources }: Props) {
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
            <span className="cursor-pointer font-semibold" onClick={() => toggleCollapse(currentPath)}>
              {collapsedNodes.has(currentPath) ? "▶ " : "▼ "} {key} ({value.length})
            </span>
            {!collapsedNodes.has(currentPath) && (
              <ul className="pl-5">{value.map((item, idx) => <li key={`${currentPath}-${idx}`}>{item}</li>)}</ul>
            )}
          </li>
        );
      } else if (typeof value === "object" && value !== null) {
        return (
          <li key={currentPath}>
            <span className="cursor-pointer font-semibold" onClick={() => toggleCollapse(currentPath)}>
              {collapsedNodes.has(currentPath) ? "▶ " : "▼ "} {key}
            </span>
            {!collapsedNodes.has(currentPath) && <ul className="pl-5">{renderTree(value, currentPath)}</ul>}
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

  return (
    <>
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
              <span className="cursor-pointer font-bold" onClick={() => toggleCollapse(res.provider)}>
                {collapsedNodes.has(res.provider) ? "▶ " : "▼ "} {res.provider}
              </span>
              {!collapsedNodes.has(res.provider) && <ul className="pl-5">{renderTree(res, res.provider)}</ul>}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
