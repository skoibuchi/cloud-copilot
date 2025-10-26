export type Message = {
  role: "user" | "ai";
  content: string;
};

export type CloudResource = {
  provider: string;
  vms?: string[];
  buckets?: string[];
  [key: string]: any;
};