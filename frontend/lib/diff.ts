import type { AnswerEdit } from "@/lib/types";

export type DiffPart =
  | { type: "same"; text: string }
  | {
      type: "replace";
      removed: string;
      added: string;
      citation: number | null;
      claimId: string;
    }
  | { type: "flag"; text: string; flag: string; citation: number | null; claimId: string };

const CITATION_SUFFIX = /\s\[(\d+)\]$/;

/** Split "text [2]" into the text and the marker, so the marker can be a link. */
export function splitCitation(text: string): string {
  return text.replace(CITATION_SUFFIX, "");
}

/** Lay the answer out as unchanged text and edits, in order. Notes are returned apart. */
export function buildDiff(
  answer: string,
  edits: AnswerEdit[],
): { parts: DiffPart[]; notes: AnswerEdit[] } {
  const placed = edits
    .filter((edit) => edit.kind !== "note" && edit.start !== null && edit.end !== null)
    .sort((a, b) => a.start! - b.start!);

  const parts: DiffPart[] = [];
  let cursor = 0;
  for (const edit of placed) {
    const start = edit.start!;
    const end = edit.end!;
    if (start < cursor || end > answer.length) continue;
    if (start > cursor) parts.push({ type: "same", text: answer.slice(cursor, start) });
    const after = splitCitation(edit.after);
    if (edit.kind === "replace") {
      parts.push({
        type: "replace",
        removed: answer.slice(start, end),
        added: after,
        citation: edit.citation,
        claimId: edit.claim_id,
      });
    } else {
      parts.push({
        type: "flag",
        text: answer.slice(start, end),
        flag: after.slice(edit.before.length).trim(),
        citation: edit.citation,
        claimId: edit.claim_id,
      });
    }
    cursor = end;
  }
  if (cursor < answer.length) parts.push({ type: "same", text: answer.slice(cursor) });

  return { parts, notes: edits.filter((edit) => edit.kind === "note") };
}
