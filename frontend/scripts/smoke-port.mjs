import { createServer } from "node:net";

export const DEFAULT_SMOKE_HOST = "127.0.0.1";
export const LEGACY_SMOKE_PORT = 3044;

function parsePort(value) {
  const port = Number(value);
  if (!Number.isInteger(port) || port <= 0 || port > 65535) {
    throw new Error("QUANTLAB_FRONTEND_SMOKE_PORT must be an integer TCP port");
  }
  return port;
}

export function requestedSmokePort(env = process.env) {
  if (env.QUANTLAB_FRONTEND_SMOKE_PORT) {
    return parsePort(env.QUANTLAB_FRONTEND_SMOKE_PORT);
  }
  return undefined;
}

export function findAvailablePort(host = DEFAULT_SMOKE_HOST) {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.unref();
    server.once("error", reject);
    server.listen(0, host, () => {
      const address = server.address();
      server.close(() => {
        if (!address || typeof address === "string") {
          reject(new Error("could not allocate a TCP port"));
          return;
        }
        resolve(address.port);
      });
    });
  });
}

export function assertPortAvailable(port, host = DEFAULT_SMOKE_HOST) {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.unref();
    server.once("error", () => {
      reject(new Error(`QUANTLAB_FRONTEND_SMOKE_PORT ${port} is already in use on ${host}`));
    });
    server.listen(port, host, () => {
      server.close(() => resolve(port));
    });
  });
}

export async function selectSmokePort(env = process.env, host = DEFAULT_SMOKE_HOST) {
  const requested = requestedSmokePort(env);
  if (requested !== undefined) {
    return await assertPortAvailable(requested, host);
  }
  return await findAvailablePort(host);
}
