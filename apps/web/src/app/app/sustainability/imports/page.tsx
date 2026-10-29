"use client";

import { useEffect, useState } from "react";
import {
  FileSpreadsheet,
  UploadCloud,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
  Activity,
  ArrowRight,
} from "lucide-react";
import { SustainabilityNav } from "../../../../components/sustainability/sustainability-nav";
import { sustainabilityService } from "../../../../services/sustainability.service";
import { SustainabilityImportBatch } from "../../../../types/sustainability";

export default function SustainabilityImportsPage() {
  const [batches, setBatches] = useState<SustainabilityImportBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string>("TANGEDCO_HighTension_PowerInvoice_June2024.csv");

  useEffect(() => {
    async function load() {
      try {
        const data = await sustainabilityService.getImportBatches();
        setBatches(data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleSimulateUpload() {
    setUploading(true);
    try {
      const batchNo = `BATCH-INVOICE-${Date.now().toString().slice(-4)}`;
      const newBatch: SustainabilityImportBatch = {
        id: `ib-${Date.now()}`,
        tenant_id: "t0000000-0000-0000-0000-000000000001",
        batch_number: batchNo,
        file_name: selectedFile,
        category: "ENERGY_INVOICE",
        total_rows: 145,
        processed_rows: 145,
        error_count: 0,
        status: "COMPLETED",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setBatches((prev) => [newBatch, ...prev]);
    } catch (err) {
      console.error("Failed to upload batch", err);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <SustainabilityNav
        title="Utility Invoice & Telemetry CSV Reconciliation Engine"
        subtitle="Batch ingestion framework integrating utility billing files, sub-meter spreadsheets, and historical consumption data."
      />

      {/* Upload Zone */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm mb-6">
        <h2 className="text-base font-bold text-slate-100 flex items-center gap-2 mb-2">
          <UploadCloud className="w-5 h-5 text-emerald-400" />
          Bulk Upload Utility Invoices & Sub-Meter Logs
        </h2>
        <p className="text-xs text-slate-400 mb-4">
          Supported file formats: CSV, TSV with automated columns for period start, period end, reading value, and tariff code.
        </p>

        <div className="border-2 border-dashed border-slate-800 hover:border-emerald-600/60 rounded-xl p-8 text-center bg-slate-950/40 transition">
          <FileSpreadsheet className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-200">
            Select or drag & drop utility invoice file
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Reconciles billed kWh against digital smart sub-meter aggregates.
          </p>

          <div className="mt-4 flex items-center justify-center gap-3">
            <input
              type="text"
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-xs text-slate-200 px-3 py-1.5 rounded-lg max-w-sm w-full"
            />
            <button
              onClick={handleSimulateUpload}
              disabled={uploading}
              className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-sm transition disabled:opacity-50"
            >
              {uploading ? "Ingesting..." : "Execute Reconciliation"}
            </button>
          </div>
        </div>
      </div>

      {/* Batches Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <FileText className="w-4 h-4 text-emerald-400" />
            Batch Reconciliation History
          </h3>
          <span className="text-xs text-slate-400">Total batches: {batches.length}</span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-20 text-slate-400">
            <Activity className="w-6 h-6 animate-spin mr-2 text-emerald-500" />
            Loading batch records...
          </div>
        ) : (
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 uppercase font-semibold">
                <th className="py-3 px-4">Batch Number</th>
                <th className="py-3 px-4">File Name</th>
                <th className="py-3 px-4">Classification</th>
                <th className="py-3 px-4">Rows Processed</th>
                <th className="py-3 px-4">Errors</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Uploaded At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {batches.map((b) => (
                <tr key={b.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-3.5 px-4 font-mono font-bold text-slate-200">
                    {b.batch_number}
                  </td>
                  <td className="py-3.5 px-4 text-slate-100 font-medium">
                    {b.file_name}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-300">
                      {b.category}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-emerald-400 font-bold">
                    {b.processed_rows} / {b.total_rows}
                  </td>
                  <td className="py-3.5 px-4">
                    {b.error_count === 0 ? (
                      <span className="text-slate-400">0</span>
                    ) : (
                      <span className="text-red-400 font-bold">{b.error_count}</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[10px] font-semibold ${
                        b.status === "COMPLETED"
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : "bg-blue-950 text-blue-400 border border-blue-800"
                      }`}
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      {b.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                    {new Date(b.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

