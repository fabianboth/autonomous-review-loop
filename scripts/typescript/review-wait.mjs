#!/usr/bin/env node
/**
 * Waits for the CodeRabbit CI action to complete on the current PR.
 * If no CI is running, exits immediately.
 *
 * Usage: node scripts/review-wait.mjs [--timeout=600]
 */
import { execSync, spawnSync } from "node:child_process";

const INITIAL_DELAY = 10_000; // 10 seconds - wait for CI to start after push
const POLL_INTERVAL = 15_000; // 15 seconds
const DEFAULT_TIMEOUT = 600_000; // 10 minutes
const RUNNING_STATES = new Set(["pending", "in_progress", "queued", "waiting", "requested"]);

function getPrNumber() {
	const result = execSync("gh pr view --json number -q .number", {
		encoding: "utf-8",
	}).trim();
	if (!result) {
		throw new Error("No PR found for current branch");
	}
	return result;
}

function getCodeRabbitCheck(prNumber) {
	const result = spawnSync(
		"gh",
		["pr", "checks", prNumber, "--json", "name,state"],
		{ encoding: "utf-8" },
	);

	if (result.status !== 0) {
		const err = (result.stderr || "").trim();
		throw new Error(`Failed to fetch PR checks: ${err || "unknown error"}`);
	}

	try {
		const checks = JSON.parse(result.stdout);
		return checks.find((c) => c.name.toLowerCase().includes("coderabbit")) ?? null;
	} catch {
		return null;
	}
}

function parseArgs() {
	const args = process.argv.slice(2);
	let timeout = DEFAULT_TIMEOUT;

	for (const arg of args) {
		if (arg.startsWith("--timeout=")) {
			const parsed = Number.parseInt(arg.split("=")[1], 10);
			if (Number.isNaN(parsed) || parsed <= 0) {
				console.error("Invalid timeout value, using default");
			} else {
				timeout = parsed * 1000;
			}
		}
	}

	return { timeout };
}

function sleep(ms) {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
	const { timeout } = parseArgs();
	const startTime = Date.now();
	const prNumber = getPrNumber();

	console.log(`Waiting ${INITIAL_DELAY / 1000}s for CI to start...`);
	await sleep(INITIAL_DELAY);

	const initialCheck = getCodeRabbitCheck(prNumber);
	const initialState = initialCheck?.state?.toLowerCase();

	if (!initialCheck || !RUNNING_STATES.has(initialState)) {
		console.log("No CodeRabbit CI in progress");
		process.exit(0);
	}

	console.log(`Waiting for CodeRabbit CI on PR #${prNumber}...`);

	while (Date.now() - startTime < timeout) {
		const check = getCodeRabbitCheck(prNumber);
		const state = check?.state?.toLowerCase();

		if (!check || !RUNNING_STATES.has(state)) {
			console.log(`\n✓ CodeRabbit CI completed${check ? ` (${check.state})` : ""}`);
			process.exit(0);
		}

		process.stdout.write(".");
		await sleep(POLL_INTERVAL);
	}

	console.log(`\n✗ Timeout after ${timeout / 1000}s`);
	process.exit(1);
}

main();
