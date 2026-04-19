const JSON_HEADERS = {
  "Content-Type": "application/json"
};

async function request(path, options = {}) {
  const response = await fetch(path, options);

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch {
      // Ignore JSON parse errors and keep the default message.
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function listIdeas(params = {}) {
  const search = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });

  const suffix = search.toString() ? `?${search.toString()}` : "";
  return request(`/ideas${suffix}`);
}

export function createIdea(payload) {
  return request("/ideas", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload)
  });
}

export function getIdea(id) {
  return request(`/ideas/${id}`);
}

export function updateIdea(id, payload) {
  return request(`/ideas/${id}`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload)
  });
}

export function archiveIdea(id) {
  return request(`/ideas/${id}`, {
    method: "DELETE"
  });
}

export function transitionIdea(id, payload) {
  return request(`/ideas/${id}/transition`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload)
  });
}

export function getIdeaEvents(id) {
  return request(`/ideas/${id}/events`);
}

export function getIdeaGraph(id) {
  return request(`/ideas/${id}/graph`);
}

export function searchIdeas(query, includeArchived = false) {
  const params = new URLSearchParams({ q: query });
  if (includeArchived) {
    params.set("include_archived", "true");
  }
  return request(`/search?${params.toString()}`);
}
