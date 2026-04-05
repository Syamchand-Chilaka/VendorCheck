"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "@/context/auth-context";
import { listVendors, createVendor } from "@/lib/api";
import type { Vendor } from "@/lib/types";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Spinner from "@/components/ui/Spinner";

export default function VendorsPage() {
  const { tenantId } = useAuth();
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!tenantId) return;
    listVendors(tenantId)
      .then((res) => setVendors(res.items))
      .catch((err) => console.error("Failed to load vendors", err))
      .finally(() => setLoading(false));
  }, [tenantId]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setError("");
    setSubmitting(true);
    try {
      const vendor = await createVendor(tenantId!, {
        name: name.trim(),
        contact_email: contactEmail.trim() || undefined,
        contact_phone: contactPhone.trim() || undefined,
      });
      setVendors((prev) => [vendor, ...prev]);
      setName("");
      setContactEmail("");
      setContactPhone("");
      setShowForm(false);
    } catch {
      setError("Failed to create vendor.");
    } finally {
      setSubmitting(false);
    }
  }

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
        <h1 className="text-2xl font-bold text-navy-900">Vendors</h1>
        <Button onClick={() => setShowForm((v) => !v)} size="sm">
          {showForm ? "Cancel" : "+ Add Vendor"}
        </Button>
      </div>

      {showForm && (
        <Card className="mb-6">
          <form onSubmit={handleCreate} className="space-y-3">
            <Input
              label="Vendor name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="Acme Plumbing LLC"
            />
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Email"
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                placeholder="billing@acme.com"
              />
              <Input
                label="Phone"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                placeholder="(555) 123-4567"
              />
            </div>
            {error && (
              <p className="text-sm text-red-700">{error}</p>
            )}
            <Button type="submit" disabled={submitting} size="sm">
              {submitting ? "Adding…" : "Add Vendor"}
            </Button>
          </form>
        </Card>
      )}

      <Card padding={false}>
        {vendors.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg font-medium">No vendors yet</p>
            <p className="text-sm mt-1">Add your first vendor to get started.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {vendors.map((vendor) => (
              <div key={vendor.id} className="px-4 py-3 flex items-center gap-4">
                <div className="h-9 w-9 rounded-full bg-gray-100 flex items-center justify-center text-sm font-medium text-gray-600">
                  {vendor.name[0]?.toUpperCase() ?? "V"}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-navy-900">{vendor.name}</p>
                  <p className="text-xs text-gray-500">
                    {vendor.contact_email ?? "No email"}{" "}
                    {vendor.contact_phone ? `· ${vendor.contact_phone}` : ""}
                  </p>
                </div>
                <span className="text-xs text-gray-400">
                  {new Date(vendor.created_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
