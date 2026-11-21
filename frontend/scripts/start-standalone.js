const { spawn } = require("node:child_process");
const fs = require("node:fs/promises");
const path = require("node:path");

const appRoot = path.resolve(__dirname, "..");
const standaloneRoot = path.join(appRoot, ".next", "standalone");

async function copyIfPresent(source, destination) {
  try {
    await fs.access(source);
  } catch (error) {
    if (error.code === "ENOENT") return;
    throw error;
  }
  await fs.mkdir(path.dirname(destination), { recursive: true });
  await fs.cp(source, destination, { recursive: true, force: true });
}

function applyRuntimeArgs(args) {
  const remaining = [];
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if ((arg === "-p" || arg === "--port") && args[index + 1]) {
      process.env.PORT = args[index + 1];
      index += 1;
    } else if ((arg === "-H" || arg === "--hostname") && args[index + 1]) {
      process.env.HOSTNAME = args[index + 1];
      index += 1;
    } else {
      remaining.push(arg);
    }
  }
  return remaining;
}

async function main() {
  const staticSource = path.join(appRoot, ".next", "static");
  await copyIfPresent(staticSource, path.join(standaloneRoot, ".next", "static"));
  await copyIfPresent(path.join(appRoot, "public"), path.join(standaloneRoot, "public"));

  const child = spawn(process.execPath, ["server.js", ...applyRuntimeArgs(process.argv.slice(2))], {
    cwd: standaloneRoot,
    env: process.env,
    stdio: "inherit",
  });

  for (const signal of ["SIGINT", "SIGTERM"]) {
    process.on(signal, () => child.kill(signal));
  }
  child.on("error", (error) => {
    console.error("Could not start the Next.js standalone server:", error.message);
    process.exitCode = 1;
  });
  child.on("exit", (code, signal) => {
    process.exitCode = code ?? (signal ? 0 : 1);
  });
}

main().catch((error) => {
  console.error("Could not prepare the Next.js standalone assets:", error.message);
  process.exitCode = 1;
});
