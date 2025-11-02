"use client";

import { useState, useEffect } from "react";
import { getToken } from "@/lib/auth";

interface AWSAccount {
  account_name: string;
  access_key: string;
  secret_key: string;
  region: string;
}

export default function AWSConfigForm() {
  const [accounts, setAccounts] = useState<AWSAccount[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL;
    const token = getToken()
    fetch(`${API_URL}/cloud/list`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => res.json())
      .then((data) => {
        const awsAccounts = data.filter((c: any) => c.provider === "aws");
        setAccounts(awsAccounts);
      });
  }, []);

  const addAccount = () => {
    setAccounts([...accounts, { account_name: "", access_key: "", secret_key: "", region: "ap-northeast-1" }]);
  };

  const updateAccount = (index: number, field: keyof AWSAccount, value: string) => {
    const newAccounts = [...accounts];
    newAccounts[index][field] = value;
    setAccounts(newAccounts);
  };

  const saveAccount = async (account: AWSAccount) => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL;
    const token = getToken()
    const res = await fetch(`${API_URL}/cloud/save`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({
        provider: "aws",
        account_name: account.account_name,
        credentials: {
          access_key: account.access_key,
          secret_key: account.secret_key,
          region: account.region,
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
            <label className="block text-sm font-medium text-gray-700">アクセスキー</label>
            <input
              value={acc.access_key}
              onChange={(e) => updateAccount(idx, "access_key", e.target.value)}
              className="mt-1 w-full border border-gray-300 rounded px-2 py-1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">シークレットキー</label>
            <input
              value={acc.secret_key}
              onChange={(e) => updateAccount(idx, "secret_key", e.target.value)}
              className="mt-1 w-full border border-gray-300 rounded px-2 py-1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">リージョン</label>
            <input
              value={acc.region}
              onChange={(e) => updateAccount(idx, "region", e.target.value)}
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
