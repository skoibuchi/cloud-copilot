"use client";

import { useState } from "react";
import CloudTabs from "@/components/CloudTabs";
import AWSConfigForm from "@/components/AWSConfigForm";
import AzureConfigForm from "@/components/AzureConfigForm"
import GCPConfigForm from "@/components/GCPConfigForm";
import IBMConfigForm from "@/components/IBMCloudConfigForm";

export default function CloudPage() {
  const [activeTab, setActiveTab] = useState("aws");

  return (
    <div className="min-h-screen bg-gray-100 py-10">
      <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-lg p-8">
        <h1 className="text-3xl font-bold mb-6 text-center">クラウド設定</h1>

        {/* タブ */}
        <CloudTabs
          activeTab={activeTab}
          setActiveTab={setActiveTab}
        />

        {/* フォームカード */}
        <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 shadow-inner transition-all">
          {activeTab === "aws" && <AWSConfigForm />}
          {activeTab === "azure" && <AzureConfigForm />}
          {activeTab === "gcp" && <GCPConfigForm />}
          {activeTab === "ibm" && <IBMConfigForm />}
        </div>
      </div>
    </div>
  );
}
