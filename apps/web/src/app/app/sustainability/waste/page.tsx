"use client";

import { useEffect, useState } from "react";
import {
  Trash2,
  Recycle,
  AlertOctagon,
  FileCheck2,
  Plus,
  Activity,
  CheckCircle2,
  Truck,
  Leaf,
} from "lucide-react";
import { SustainabilityNav } from "../../../../components/sustainability/sustainability-nav";
import { sustainabilityService } from "../../../../services/sustainability.service";
import { WasteCategory, WasteDisposalMethod, WasteRecord } from "../../../../types/sustainability";

export default function SustainabilityWastePage() {
  const [wasteRecords, setWasteRecords] = useState<WasteRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [showLogModal, setShowLogModal] = useState(false);

  // Form State
  const [wasteCode, setWasteCode] = useState("");
  const [category, setCategory] = useState<WasteCategory>("ORGANIC_COMPOST");
  const [isHazardous, setIsHazardous] = useState(false);
  const [quantity, setQuantity] = useState(500);
  const [unit, setUnit] = useState("kg");
  const [disposalMethod, setDisposalMethod] = useState<WasteDisposalMethod>("COMPOSTING");
  const [partner, setPartner] = useState("Campus Agro Vermicompost Unit");
  const [manifestNo, setManifestNo] = useState("");
  const [certRef, setCertRef] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await sustainabilityService.getWasteRecords();
        setWasteRecords(data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleLog(e: React.FormEvent) {
    e.preventDefault();
    try {
      const code = wasteCode || `WST-${Date.now().toString().slice(-4)}`;
      const created = await sustainabilityService.recordWaste({
        campus_id: "c0000000-0000-0000-0000-000000000001",
        waste_code: code,
        waste_category: category,
        is_hazardous: isHazardous,
        quantity: Number(quantity),
        unit,
        collection_date: new Date().toISOString().split("T")[0],
        disposal_method: disposalMethod,
        partner_name: partner,
        manifest_number: manifestNo || undefined,
        certificate_ref: certRef || undefined,
      });
      setWasteRecords((prev) => [created, ...prev]);
      setShowLogModal(false);
      setWasteCode("");
      setManifestNo("");
      setCertRef("");
    } catch (err) {
      console.error("Failed to log waste record", err);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <SustainabilityNav
        title="Campus Solid, Organic & Regulated Hazardous Waste Manifests"
        subtitle="Tracking campus zero-waste diversion, organic composting, e-waste EPR stewardship, and authorized TSDF hazardous disposal."
      />

      {/* Diversion Ledger Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Diversion Rate</span>
            <span className="p-2 rounded-lg bg-emerald-950 text-emerald-400 border border-emerald-800">
              <Recycle className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-400">71.8%</div>
          <p className="text-xs text-slate-400 mt-1">Diverted away from municipal landfills</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Organic Composted</span>
            <span className="p-2 rounded-lg bg-green-950 text-green-400 border border-green-800">
              <Leaf className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-100">4,250 kg</div>
          <p className="text-xs text-slate-400 mt-1">Mess food waste into rich vermicompost</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">E-Waste Recycled</span>
            <span className="p-2 rounded-lg bg-blue-950 text-blue-400 border border-blue-800">
              <Truck className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2 text-2xl font-bold text-blue-400">680 kg</div>
          <p className="text-xs text-slate-400 mt-1">CPCB certified EPR recycling partner</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Hazardous TSDF</span>
            <span className="p-2 rounded-lg bg-red-950 text-red-400 border border-red-800">
              <AlertOctagon className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2 text-2xl font-bold text-red-400">240 kg</div>
          <p className="text-xs text-slate-400 mt-1">SPCB Form 10 certified disposal</p>
        </div>
      </div>

      {/* Manifests & Records Table */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <FileCheck2 className="w-4 h-4 text-emerald-400" />
            Verified Waste Disposal & Manifest Ledger
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Chain-of-custody tracking with verified vendor recycling certificates.
          </p>
        </div>
        <button
          onClick={() => setShowLogModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-sm transition"
        >
          <Plus className="w-4 h-4" /> Log Waste Manifest
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-20 text-slate-400">
          <Activity className="w-6 h-6 animate-spin mr-2 text-emerald-500" />
          Loading waste manifests...
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 uppercase font-semibold">
                <th className="py-3 px-4">Waste Code</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Quantity</th>
                <th className="py-3 px-4">Disposal Method</th>
                <th className="py-3 px-4">Collection Partner</th>
                <th className="py-3 px-4">Manifest / Certificate</th>
                <th className="py-3 px-4">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {wasteRecords.map((w) => (
                <tr key={w.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-3.5 px-4 font-mono font-bold text-slate-200">
                    {w.waste_code}
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold ${
                        w.is_hazardous
                          ? "bg-red-950 text-red-400 border border-red-800"
                          : "bg-emerald-950 text-emerald-400 border border-emerald-800"
                      }`}
                    >
                      {w.is_hazardous && <AlertOctagon className="w-3 h-3" />}
                      {w.waste_category.replace("_", " ")}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-bold text-slate-100">
                    {w.quantity.toLocaleString()} {w.unit}
                  </td>
                  <td className="py-3.5 px-4 text-slate-300">
                    {w.disposal_method.replace("_", " ")}
                  </td>
                  <td className="py-3.5 px-4 text-slate-300 font-medium">
                    {w.partner_name}
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="font-mono text-[11px] text-slate-200">
                      {w.manifest_number || "—"}
                    </div>
                    {w.certificate_ref && (
                      <div className="text-[10px] text-emerald-400 font-medium">{w.certificate_ref}</div>
                    )}
                  </td>
                  <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                    {w.collection_date}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Log Modal */}
      {showLogModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-xl">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Trash2 className="w-5 h-5 text-emerald-400" />
              Log Waste Generation & Disposal Manifest
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Verify legal chain-of-custody for non-hazardous circularity and hazardous TSDF disposal.
            </p>

            <form onSubmit={handleLog} className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Waste Classification</label>
                  <select
                    value={category}
                    onChange={(e) => {
                      const val = e.target.value as WasteCategory;
                      setCategory(val);
                      if (val === "HAZARDOUS_CHEMICAL" || val === "BIO_MEDICAL") {
                        setIsHazardous(true);
                        setDisposalMethod("AUTHORIZED_HAZARDOUS_TSDF");
                      } else {
                        setIsHazardous(false);
                      }
                    }}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  >
                    <option value="ORGANIC_COMPOST">Organic Compostable (Mess)</option>
                    <option value="RECYCLABLE_PLASTIC">Recyclable Plastic</option>
                    <option value="RECYCLABLE_PAPER">Recyclable Paper / Cardboard</option>
                    <option value="E_WASTE">E-Waste (Computers, Batteries)</option>
                    <option value="HAZARDOUS_CHEMICAL">Hazardous Chemical (Labs)</option>
                    <option value="GENERAL">General Municipal Waste</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Disposal Method</label>
                  <select
                    value={disposalMethod}
                    onChange={(e) => setDisposalMethod(e.target.value as WasteDisposalMethod)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  >
                    <option value="COMPOSTING">On-Campus Vermicomposting</option>
                    <option value="RECYCLING_VENDOR">Authorized Recycler Vendor</option>
                    <option value="AUTHORIZED_EWASTE_FACILITY">CPCB E-Waste Facility</option>
                    <option value="AUTHORIZED_HAZARDOUS_TSDF">Authorized TSDF Incineration</option>
                    <option value="MUNICIPAL_LANDFILL">Municipal Landfill</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Quantity</label>
                  <input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(Number(e.target.value))}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Unit</label>
                  <input
                    type="text"
                    value={unit}
                    onChange={(e) => setUnit(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Partner / Vendor Name</label>
                <input
                  type="text"
                  required
                  value={partner}
                  onChange={(e) => setPartner(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Manifest Number</label>
                  <input
                    type="text"
                    placeholder="e.g. TNWML-MAN-8821"
                    value={manifestNo}
                    onChange={(e) => setManifestNo(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Disposal Certificate Ref</label>
                  <input
                    type="text"
                    placeholder="e.g. CERT-TSDF-2024"
                    value={certRef}
                    onChange={(e) => setCertRef(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowLogModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white"
                >
                  Save Manifest
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

