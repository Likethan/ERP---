"use client";

import { useEffect, useState } from "react";
import {
  Cpu,
  Wifi,
  Activity,
  Plus,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Server,
} from "lucide-react";
import { SustainabilityNav } from "../../../../components/sustainability/sustainability-nav";
import { sustainabilityService } from "../../../../services/sustainability.service";
import { IoTIngestionEvent, IoTMeterStream, ResourceType } from "../../../../types/sustainability";

export default function SustainabilityIoTMetersPage() {
  const [meters, setMeters] = useState<IoTMeterStream[]>([]);
  const [events, setEvents] = useState<IoTIngestionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [simulating, setSimulating] = useState(false);

  // Form State
  const [deviceId, setDeviceId] = useState("");
  const [deviceName, setDeviceName] = useState("");
  const [building, setBuilding] = useState("Technology Tower Alpha");
  const [meterType, setMeterType] = useState<ResourceType>("ELECTRICITY_GRID");
  const [protocol, setProtocol] = useState("MQTT");

  useEffect(() => {
    async function load() {
      try {
        const data = await sustainabilityService.getIoTMeters();
        setMeters(data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    try {
      const devId = deviceId || `DEV-${Date.now().toString().slice(-4)}`;
      const created = await sustainabilityService.registerIoTMeter({
        device_id: devId,
        device_name: deviceName || `Meter ${devId}`,
        campus_id: "c0000000-0000-0000-0000-000000000001",
        building_name: building,
        meter_type: meterType,
        protocol,
        sampling_interval_secs: 300,
      });
      setMeters((prev) => [created, ...prev]);
      setShowRegisterModal(false);
      setDeviceId("");
      setDeviceName("");
    } catch (err) {
      console.error("Failed to register IoT meter", err);
    }
  }

  async function handleSimulateTelemetry(meter: IoTMeterStream) {
    setSimulating(true);
    try {
      const reading = Number((300 + Math.random() * 200).toFixed(1));
      const ev = await sustainabilityService.ingestTelemetry({
        device_id: meter.device_id,
        event_timestamp: new Date().toISOString(),
        metric_name: "active_power_kwh",
        metric_value: reading,
        unit: "kWh",
        raw_payload: { simulated: true, signal_dbm: -64 },
      });
      setEvents((prev) => [ev, ...prev]);
    } catch (err) {
      console.error("Failed to simulate telemetry", err);
    } finally {
      setSimulating(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <SustainabilityNav
        title="IoT Smart Meter Telemetry Streams & Cryptographic Ingestion"
        subtitle="Edge-to-cloud automated telemetry ingestion over MQTT / Modbus with cryptographic SHA-256 deduplication."
      />

      {/* Control Bar */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyan-400" />
            Registered IoT Energy & Water Gateway Nodes
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Streaming real-time campus microgrid and ultrasonic flow measurements.
          </p>
        </div>
        <button
          onClick={() => setShowRegisterModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-sm transition"
        >
          <Plus className="w-4 h-4" /> Provision IoT Meter
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-20 text-slate-400">
          <Activity className="w-6 h-6 animate-spin mr-2 text-emerald-500" />
          Loading IoT sensor network...
        </div>
      ) : (
        <div className="space-y-6">
          {/* Smart Meters Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {meters.map((meter) => (
              <div
                key={meter.id}
                className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <span className="text-[11px] font-mono text-cyan-400 font-bold">
                      {meter.device_id}
                    </span>
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded ${
                        meter.status === "ONLINE"
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : "bg-red-950 text-red-400 border border-red-800"
                      }`}
                    >
                      <Wifi className="w-3 h-3" />
                      {meter.status}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-100 mt-2">{meter.device_name}</h3>
                  <p className="text-xs text-slate-400 mt-1">{meter.building_name}</p>
                </div>

                <div className="mt-4 pt-4 border-t border-slate-800/80 space-y-2 text-xs">
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Protocol / Bus:</span>
                    <span className="font-mono text-slate-200">{meter.protocol}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Latest Telemetry Reading:</span>
                    <span className="font-bold text-emerald-400 font-mono">
                      {meter.last_reading_value ? `${meter.last_reading_value} kWh` : "Live Feed Active"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                    <span>Sampling Interval: {meter.sampling_interval_secs}s</span>
                    <button
                      onClick={() => handleSimulateTelemetry(meter)}
                      disabled={simulating}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-cyan-400 hover:text-cyan-300"
                    >
                      <RefreshCw className="w-3 h-3" /> Pulse Test
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Real-time Ingestion Stream Logs */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2 mb-2">
              <Server className="w-5 h-5 text-emerald-400" />
              Cryptographic Ingestion Stream & De-duplication Log
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Events are authenticated and evaluated with SHA-256 seed hashing to eliminate duplicate wireless bursts.
            </p>

            <div className="space-y-2 font-mono text-xs">
              {events.length === 0 ? (
                <div className="p-4 bg-slate-950/60 rounded-lg text-slate-500 text-center italic">
                  Click &apos;Pulse Test&apos; on any device above to simulate authenticated live telemetry events.
                </div>
              ) : (
                events.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-3 bg-slate-950/80 rounded-lg border border-slate-800/80 flex items-center justify-between text-slate-300"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-2 h-2 rounded-full bg-emerald-400" />
                      <span className="text-cyan-400">{ev.device_id}</span>
                      <span className="text-slate-400">metric: {ev.metric_name}</span>
                      <span className="font-bold text-emerald-400">
                        {ev.metric_value} {ev.unit}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-[11px] text-slate-500">
                      <span>Status: {ev.ingestion_status}</span>
                      <span className="text-slate-600 truncate max-w-xs">{ev.dedup_hash}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Provision Modal */}
      {showRegisterModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-xl">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-cyan-400" />
              Provision IoT Smart Meter Gateway
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Configure device metadata and industrial communication bus.
            </p>

            <form onSubmit={handleRegister} className="mt-4 space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300">Device Hardware ID</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. MTR-SMART-ENG-03"
                  value={deviceId}
                  onChange={(e) => setDeviceId(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Device Friendly Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Engineering Block 3 Feeder Meter"
                  value={deviceName}
                  onChange={(e) => setDeviceName(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Building / Zone</label>
                <input
                  type="text"
                  value={building}
                  onChange={(e) => setBuilding(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Meter Type</label>
                  <select
                    value={meterType}
                    onChange={(e) => setMeterType(e.target.value as ResourceType)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  >
                    <option value="ELECTRICITY_GRID">Electricity Grid</option>
                    <option value="SOLAR_GENERATION">Rooftop Solar PV</option>
                    <option value="WATER_MUNICIPAL">Water Flow Meter</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Protocol</label>
                  <select
                    value={protocol}
                    onChange={(e) => setProtocol(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  >
                    <option value="MQTT">MQTT</option>
                    <option value="MODBUS_TCP">Modbus TCP</option>
                    <option value="HTTP_REST">HTTP REST</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowRegisterModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white"
                >
                  Register Device
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

