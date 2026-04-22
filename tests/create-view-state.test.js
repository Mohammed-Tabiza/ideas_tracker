import test from "node:test";
import assert from "node:assert/strict";

import {
  EMPTY_FILTERS,
  buildViewStateAfterIdeaCreate
} from "../src/createViewState.js";

test("buildViewStateAfterIdeaCreate resets search and portfolio filters", () => {
  const state = buildViewStateAfterIdeaCreate({
    filters: {
      status: "GERME",
      domain: "ARCHITECTURE",
      tags: "llm, infra",
      stale: true,
      revisit_before: "2026-04-20",
      sort: "created_at",
      order: "asc"
    },
    searchMode: true,
    searchQuery: "pageindex"
  });

  assert.deepEqual(state, {
    filters: EMPTY_FILTERS,
    searchMode: false,
    searchQuery: ""
  });
});
