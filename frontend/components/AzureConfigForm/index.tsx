"use client";

import { useState, useEffect } from "react";
import { getToken } from "@/lib/auth";

interface AzureAccount {
  account_name: string;
  tenant_id: string;
  client_id: string;
  client_secret: string;
  subscription_id: string;
}

export default function AzureConfigForm() {
  const [accounts, setAccounts] = useState<AzureAccount[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL;
    const token = getToken()
    fetch(`${API_URL}/cloud/list`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => res.json())
      .then((data) => {
        const azureAccounts = data.filter((c: any) => c.provider === "azure");
        setAccounts(azureAccounts);
      });
  }, []);

  const addAccount = () => {
    setAccounts([
      ...accounts,
      {
        account_name: "",
        tenant_id: "",
        client_id: "",
        client_secret: "",
        subscription_id: "",
      },
    ]);
  };

  const updateAccount = (index: number, field: keyof AzureAccount, value: string) => {
    const newAccounts = [...accounts];
    newAccounts[index][field] = value;
    setAccounts(newAccounts);
  };

  const saveAccount = async (account: AzureAccount) => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL;
    const token = getToken()
    const res = await fetch(`${API_URL}/cloud/save`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({
        provider: "azure",
        account_name: account.account_name,
        credentials: {
          tenant_id: account.tenant_id,
          client_id: account.client_id,
          client_secret: account.client_secret,
          subscription_id: account.subscription_id,
        },
      }),
    });
    if (res.ok) setMessage("保存しました！");
    else setMessage("保存に失敗しました。");
  };

  return (
    <div className="space-y-4">
      {accounts.map((acc, idx) => (
        <div key={idx} className="bg-white shadow-md border rounded-lg p-4 space-y-2">
          <div>
            <label className="block text-sm font-medium text-gray-700">アカウント名</label>
            <input
              value={acc.account_name}
              onChange={(e) => updateAccount(idx, "account_name", e.target.value)}
              className="mt-1 w-full border border-gray-300 rounded px-2 py-1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">テナントID</label>
            <input
              value={acc.tenant_id}
              onChange={(e) => updateAccount(idx, "tenant_id", e.target.value)}
              className="mt-1 w-full border border-gray-300 rounded px-2 py-1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">クライアントID</label>
            <input
              value={acc.client_id}
              onChange={(e) => updateAccount(idx, "client_id", e.target.value)}
              className="mt-1 w-full border border-gray-300 rounded px-2 py-1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">クライアントシークレット</label>
            <input
              value={acc.client_secret}
              onChange={(e) => updateAccount(idx, "client_secret", e.target.value)}
              className="mt-1 w-full border border-gray-300 rounded px-2 py-1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">サブスクリプションID</label>
            <input
              value={acc.subscription_id}
              onChange={(e) => updateAccount(idx, "subscription_id", e.target.value)}
              className="mt-1 w-full border border-gray-300 rounded px-2 py-1"
            />
          </div>
          <button
            className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded mt-2 cursor-pointer"
            onClick={() => saveAccount(acc)}
          >
            保存
          </button>
        </div>
      ))}

      <button
        className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded mt-2 cursor-pointer"
        onClick={addAccount}
      >
        アカウント追加
      </button>

      {message && <p className="text-sm text-gray-700 mt-2">{message}</p>}
    </div>
  );
}
