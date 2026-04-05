"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { listReviewTasks, resolveReviewTask } from "@/lib/api";
import type { ReviewTask } from "@/lib/types";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";

export default function ReviewsPage() {
  const { tenantId } = useAuth();
  const [tasks, setTasks] = useState<ReviewTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState<string | null>(null);

  useEffect(() => {
    if (!tenantId) return;
    listReviewTasks(tenantId)
      .then((res) => setTasks(res.items))
      .catch((err) => console.error("Failed to load review tasks", err))
      .finally(() => setLoading(false));
  }, [tenantId]);

  async function handleResolve(taskId: string, resolution: string) {
    if (!tenantId) return;
    setResolving(taskId);
    try {
      await resolveReviewTask(tenantId, taskId, resolution);
      setTasks((prev) =>
        prev.map((t) =>
          t.id === taskId ? { ...t, status: "resolved", resolution } : t,
        ),
      );
    } catch (err) {
      console.error("Failed to resolve task", err);
    } finally {
      setResolving(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  const open = tasks.filter((t) => t.status === "open");
  const resolved = tasks.filter((t) => t.status !== "open");

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-navy-900">Review Tasks</h1>
        <Badge variant="info">{open.length} open</Badge>
      </div>

      {/* Open tasks */}
      {open.length > 0 && (
        <div className="mb-8">
          <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
            Needs Review
          </h2>
          <div className="space-y-3">
            {open.map((task) => (
              <Card key={task.id}>
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="verify">Priority {task.priority}</Badge>
                      <span className="text-xs text-gray-500">
                        {new Date(task.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">
                      {task.document_id
                        ? `Document review required`
                        : `Check review required`}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="primary"
                      disabled={resolving === task.id}
                      onClick={() => handleResolve(task.id, "approved")}
                    >
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      disabled={resolving === task.id}
                      onClick={() => handleResolve(task.id, "rejected")}
                    >
                      Reject
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Resolved tasks */}
      {resolved.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">
            Resolved
          </h2>
          <Card padding={false}>
            <div className="divide-y divide-gray-100">
              {resolved.map((task) => (
                <div key={task.id} className="px-4 py-3 flex items-center gap-4">
                  <div className="flex-1">
                    <p className="text-sm text-gray-600">
                      {task.document_id ? "Document" : "Check"} review
                    </p>
                    <p className="text-xs text-gray-400">
                      {task.resolved_at
                        ? new Date(task.resolved_at).toLocaleString()
                        : ""}
                    </p>
                  </div>
                  <Badge
                    variant={task.resolution === "approved" ? "safe" : "blocked"}
                  >
                    {task.resolution ?? "resolved"}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {tasks.length === 0 && (
        <Card>
          <div className="text-center py-8 text-gray-500">
            <p className="text-lg font-medium">No review tasks</p>
            <p className="text-sm mt-1">
              Review tasks are created when documents require manual verification.
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}
