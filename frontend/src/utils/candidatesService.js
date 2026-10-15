/**
 * Candidate data service. The UI asks for a pool by id; where it comes from is decided by
 * VITE_CANDIDATES_PROVIDER:
 *
 *   local (default)  bundled sample candidates (src/data)
 *   api              GET /candidates?pool=<id> on the backend (MongoDB Atlas) -> Candidate[]
 *
 * Candidate objects keep the exact shape of src/data/candidatesData.js, so the backend only has to
 * return documents of that shape.
 */
import { config, isApiMode } from "../config/env";
import { api } from "./apiClient";
import { inrOnlyPool } from "./money";
import { CANDIDATES_12, CANDIDATES_50, CANDIDATES_100 } from "../data/candidatesData";

export const POOLS = {
  core12: { id: "core12", label: "12 Core Suite", count: 12 },
  benchmark50: { id: "benchmark50", label: "50 Benchmark Resumes Pool", count: 50 },
  benchmark100: { id: "benchmark100", label: "100 Enterprise Benchmark Suite", count: 100 },
};

const LOCAL = {
  core12: inrOnlyPool(CANDIDATES_12),
  benchmark50: inrOnlyPool(CANDIDATES_50),
  benchmark100: inrOnlyPool(CANDIDATES_100),
};

export const INITIAL_POOL = LOCAL.core12;

export const candidatesService = {
  async loadPool(poolId) {
    if (!POOLS[poolId]) throw new Error(`Unknown candidate pool: ${poolId}`);
    if (isApiMode(config.candidatesProvider)) {
      return inrOnlyPool(await api.get(`/candidates?pool=${encodeURIComponent(poolId)}`));
    }
    return LOCAL[poolId];
  },
};
