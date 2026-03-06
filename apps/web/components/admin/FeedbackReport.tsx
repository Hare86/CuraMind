import type { IFeedback } from "@/lib/types";

interface FeedbackReportProps {
  feedbacks: IFeedback[];
}

const RATING_STYLES: Record<string, string> = {
  useful: "bg-green-100 text-green-700",
  incorrect: "bg-red-100 text-red-700",
  needs_review: "bg-amber-100 text-amber-700",
};

export default function FeedbackReport({ feedbacks }: FeedbackReportProps) {
  if (!feedbacks.length) {
    return <p className="text-sm text-gray-500 py-4">No low-rated responses.</p>;
  }

  return (
    <div className="space-y-3">
      {feedbacks.map((fb) => (
        <div key={fb.id} className="border border-gray-200 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${RATING_STYLES[fb.rating] ?? ""}`}>
              {fb.rating.replace("_", " ")}
            </span>
            {fb.query_mode && (
              <span className="text-xs text-gray-400">{fb.query_mode}</span>
            )}
            <span className="text-xs text-gray-400 ml-auto">
              {new Date(fb.created_at).toLocaleDateString()}
            </span>
          </div>
          {fb.comment && (
            <p className="text-xs text-gray-600">{fb.comment}</p>
          )}
        </div>
      ))}
    </div>
  );
}
