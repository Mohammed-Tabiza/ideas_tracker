export const STATUS_OPTIONS = [
  "GERME",
  "EXPLORATION",
  "POC",
  "TRANSMIS",
  "EN_VEILLE",
  "ABANDONNE",
  "REALISE"
];

export const DOMAIN_OPTIONS = [
  "OTHER",
  "IA4IT",
  "IA4ALL",
  "STRATEGY",
  "ARCHITECTURE"
];

export const SOURCE_TYPE_OPTIONS = [
  "INTUITION",
  "CONVERSATION",
  "MEETING",
  "READING",
  "EXPERIMENT",
  "OTHER"
];

export const SORT_OPTIONS = [
  { value: "created_at", label: "Creation" },
  { value: "last_activity", label: "Derniere activite" },
  { value: "estimated_value", label: "Valeur estimee" }
];

export const ORDER_OPTIONS = [
  { value: "desc", label: "Desc" },
  { value: "asc", label: "Asc" }
];

export const ALLOWED_TRANSITIONS = {
  GERME: ["EXPLORATION", "ABANDONNE"],
  EXPLORATION: ["POC", "EN_VEILLE", "ABANDONNE"],
  POC: ["TRANSMIS", "EN_VEILLE", "ABANDONNE"],
  TRANSMIS: ["REALISE", "EN_VEILLE"],
  EN_VEILLE: ["EXPLORATION", "ABANDONNE"],
  ABANDONNE: ["EXPLORATION"],
  REALISE: []
};

export const REASON_CODES = {
  EN_VEILLE: ["TOO_EARLY", "NO_PRIORITY", "WAITING_DEPENDENCY"],
  ABANDONNE: ["NO_VALUE", "TOO_COMPLEX", "DUPLICATE", "CONTEXT_CHANGED"]
};
