#!/usr/bin/env node
import { execSync, spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";

const GRAPHQL_QUERY = `query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviews(first: 50) {
        nodes {
          id
          databaseId
          author { login }
          body
          reactions(first: 10) {
            nodes { user { login } content }
          }
        }
      }
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 1) {
            nodes { author { login } path line body }
          }
        }
      }
    }
  }
}`.replace(/\n/g, " ");

// Strip HTML comments from review body
function stripHtmlComments(body) {
	return body.replace(/<!--[\s\S]*?-->/g, "").trim();
}

function runGraphQL(query, variables) {
	const args = ["api", "graphql"];
	for (const [key, value] of Object.entries(variables)) {
		args.push("-F", `${key}=${value}`);
	}
	args.push("-f", `query=${query}`);

	const result = spawnSync("gh", args, { encoding: "utf-8" });
	if (result.status !== 0) {
		throw new Error(result.stderr || "GraphQL query failed");
	}
	try {
		return JSON.parse(result.stdout);
	} catch {
		throw new Error(`Failed to parse GraphQL response: ${result.stdout.slice(0, 200)}`);
	}
}

function getCurrentUser() {
	const result = execSync("gh api user -q .login", { encoding: "utf-8" });
	return result.trim();
}

function getRepoInfo() {
	return JSON.parse(
		execSync("gh repo view --json owner,name", { encoding: "utf-8" }),
	);
}

function getPrNumber() {
	const result = execSync("gh pr view --json number -q .number", {
		encoding: "utf-8",
	}).trim();
	if (!result) {
		throw new Error("No PR found for current branch");
	}
	return result;
}

// Check if user has reacted to a review
function hasUserReacted(review, username) {
	return review.reactions.nodes.some(
		(r) => r.user?.login === username && r.content === "THUMBS_UP",
	);
}

// Add thumbs up reaction to a review
function addReactionToReview(reviewId) {
	const mutation = `mutation($id: ID!) {
		addReaction(input: {subjectId: $id, content: THUMBS_UP}) {
			reaction { content }
		}
	}`.replace(/\n/g, " ");

	return runGraphQL(mutation, { id: reviewId });
}

function main() {
	const command = process.argv[2];

	const repoInfo = getRepoInfo();
	const prNumber = getPrNumber();
	const currentUser = getCurrentUser();

	// Fetch data
	const result = runGraphQL(GRAPHQL_QUERY, {
		owner: repoInfo.owner.login,
		repo: repoInfo.name,
		pr: prNumber,
	});

	const prData = result.data.repository.pullRequest;

	// Get CodeRabbit reviews that user hasn't reacted to yet
	const coderabbitReviews = prData.reviews.nodes.filter(
		(r) => r.author?.login === "coderabbitai" && r.body,
	);

	const unreactedReviews = coderabbitReviews.filter(
		(r) => !hasUserReacted(r, currentUser),
	);

	// Default: fetch and display comments
	// Get ALL unresolved inline threads (any author)
	const unresolvedThreads = prData.reviewThreads.nodes.filter(
		(t) => !t.isResolved && t.comments.nodes[0],
	);

	// Get full body from unreacted CodeRabbit reviews (stripped of HTML comments)
	const reviewBodies = unreactedReviews
		.map((r) => ({ id: r.id, body: stripHtmlComments(r.body) }))
		.filter((r) => r.body.length > 0);

	const hasContent = unresolvedThreads.length > 0 || reviewBodies.length > 0;

	if (!hasContent) {
		mkdirSync(".reviews", { recursive: true });
		writeFileSync(
			".reviews/prComments.md",
			`# Review Comments\n\n**PR:** #${prNumber}\n\n✅ No unresolved comments.\n`,
		);
		console.log("No unresolved comments found on this PR");
		return;
	}

	// Build output
	let output = `# Review Comments

**PR:** #${prNumber}
**Inline threads (unresolved):** ${unresolvedThreads.length}
**Review comments (unreacted):** ${reviewBodies.length}

To resolve an inline thread after addressing it:
\`\`\`bash
gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "THREAD_ID"}) { thread { isResolved } } }'
\`\`\`

To mark a review as addressed (adds 👍 reaction):
\`\`\`bash
gh api graphql -f query='mutation { addReaction(input: {subjectId: "REVIEW_ID", content: THUMBS_UP}) { reaction { content } } }'
\`\`\`

`;

	// Inline threads section
	if (unresolvedThreads.length > 0) {
		output += `---\n\n# Inline Comments (Unresolved)\n\n`;
		output += unresolvedThreads
			.map((t) => {
				const comment = t.comments.nodes[0];
				const location = `${comment.path}:${comment.line ?? "?"}`;
				const author = comment.author?.login ?? "unknown";
				return `## ${location}\n\n**Thread ID:** \`${t.id}\`\n**Author:** ${author}\n\n${comment.body}`;
			})
			.join("\n\n---\n\n");
	}

	// Review bodies section (full text from unreacted reviews)
	if (reviewBodies.length > 0) {
		output += `\n\n---\n\n# Review Comments (${reviewBodies.length})\n\n`;
		output += reviewBodies
			.map((r) => `**Review ID:** \`${r.id}\`\n\n${r.body}`)
			.join("\n\n---\n\n");
	}

	// Write to file
	mkdirSync(".reviews", { recursive: true });
	writeFileSync(".reviews/prComments.md", output);
	console.log(`Saved review comments to .reviews/prComments.md:`);
	console.log(`  - ${unresolvedThreads.length} unresolved inline threads`);
	console.log(`  - ${reviewBodies.length} review comments`);
}

try {
	main();
} catch (error) {
	console.error("Error:", error.message);
	process.exit(1);
}
