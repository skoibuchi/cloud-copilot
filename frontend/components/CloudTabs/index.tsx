"use client";

interface Props {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export default function CloudTabs({ activeTab, setActiveTab }: Props) {
  const tabs = ["aws", "azure", "gcp", "ibm"];
  return (
    <div className="flex border-b border-gray-300 mb-4">
      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => setActiveTab(tab)}
          className={`
            px-5 py-2 -mb-px border-b-2
            font-medium text-gray-600
            transition-colors duration-300
            cursor-pointer
            ${activeTab === tab 
              ? "border-blue-500 text-blue-600 font-bold" 
              : "border-transparent hover:text-blue-500 hover:border-blue-300"}
          `}
        >
          {tab.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
