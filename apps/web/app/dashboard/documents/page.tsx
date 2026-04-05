"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { listDocuments } from "@/lib/api";
import type { DocumentItem } from "@/lib/types";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";

const STATUS_VARIANT: Record<string, "safe" | "verify" | "blocked" | "neutral" | "info"> = {
  uploaded: "neutral",
  queued: "info",
  validated: "safe",
  review_needed: "verify",
  rejected: "blocked",
};

export default function DocumentsPage() {
  const { tenantId } = useAuth();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tenantId) return;
    listDocuments(tenantId)
      .then((res) => setDocuments(res.items))
      .catch((err) => console.error("Failed to load documents", err))
      .finally(() => setLoading(false));
  }, [tenantId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-navy-900">Documents</h1>
      </div>

      <Card padding={false}>
        {documents.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg font-medium">No documents yet</p>
            <p className="text-sm mt-1">
              Documents uploaded via the API will appear here.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {documents.map((doc) => (
              <div key={doc.id} className="px-4 py-3 flex items-center gap-4">
                <svg className="w-8 h-8 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-navy-900">
                    {doc.title ?? "Untitled"}
                  </p>
                  <p className="text-xs text-gray-500">
                    {doc.document_type ?? "document"} · v{doc.current_version_no}
                  </p>
                </div>
                <Badge variant={STATUS_VARIANT[doc.status] ?? "neutral"}>
                  {doc.status.replace("_", " ")}
                </Badge>
                <span className="text-xs text-gray-400">
                  {new Date(doc.created_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
