export function formatDateTime(value) {
  if (!value) {
    return "--";
  }

  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function formatDate(value) {
  if (!value) {
    return "--";
  }

  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium"
  }).format(new Date(value));
}

export function toInputDateTime(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export function fromInputDateTime(value) {
  if (!value) {
    return null;
  }

  return new Date(value).toISOString();
}

export function serializeTags(value) {
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

export function relativeStaleText(updatedAt) {
  if (!updatedAt) {
    return "Aucune activite";
  }

  const elapsed = Date.now() - new Date(updatedAt).getTime();
  const days = Math.floor(elapsed / (1000 * 60 * 60 * 24));
  if (days <= 0) {
    return "Mis a jour aujourd'hui";
  }
  if (days === 1) {
    return "Mis a jour hier";
  }
  return `Mis a jour il y a ${days} jours`;
}
