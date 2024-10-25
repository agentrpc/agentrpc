import debug from "debug";
import { machineIdSync } from "node-machine-id";
import { createHash } from "crypto";

const log = debug("inferable:machine-id");

let cachedId: string | undefined;

export const machineId = () => {
  if (cachedId) {
    return cachedId;
  }

  try {
    const id = machineIdSync();
    const hash = createHash("shake256", {
      outputLength: 8,
    })
      .update(id)
      .digest("hex");

    cachedId = hash;

    return hash;
  } catch (e) {
    log("Failed to get machine ID. Defaulting to random string.", { error: e });

    const str = Math.random().toString(36).substring(8);
    cachedId = str;

    return str;
  }
};
