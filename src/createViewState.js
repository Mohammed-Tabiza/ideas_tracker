export const EMPTY_FILTERS = {
  status: "",
  domain: "",
  tags: "",
  stale: false,
  revisit_before: "",
  sort: "last_activity",
  order: "desc"
};

export function buildViewStateAfterIdeaCreate() {
  return {
    filters: { ...EMPTY_FILTERS },
    searchMode: false,
    searchQuery: ""
  };
}
