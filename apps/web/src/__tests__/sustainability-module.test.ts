/**
 * CampusOS — Enterprise Campus Sustainability, Energy Management, Environmental Compliance & Carbon Intelligence Test Suite (Step 67)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 *
 * Automated verification suite validating:
 * 1. Sustainability master profiles and quantitative reduction targets.
 * 2. Emission factor registry with IPCC AR5 warming standards.
 * 3. Resource measurements and automated peak load anomaly detection (>30% WARNING, >50% CRITICAL).
 * 4. Water resources balance, loss quantification, and leak incident repair workflow.
 * 5. Waste generation circularity, composting diversion, and authorized TSDF hazardous manifests.
 * 6. GHG Protocol Scope 1, 2, 3 carbon accounting calculations with MT conversion.
 * 7. Green sustainability initiatives portfolio and avoided carbon accounting.
 * 8. Statutory environmental compliance permits (SPCB CTO, CGWA NOC) and CAPA management.
 * 9. IoT smart meter gateway devices and live telemetry ingestion.
 * 10. Utility invoice CSV reconciliation batches.
 * 11. Institutional ESG composite scorecard overview metrics.
 */

import { sustainabilityService } from "../services/sustainability.service";
import {
  MOCK_CAMPUS_ID,
  MOCK_DASHBOARD_OVERVIEW,
  MOCK_EMISSION_FACTORS,
  MOCK_INITIATIVES,
  MOCK_IOT_METERS,
  MOCK_MEASUREMENTS,
  MOCK_PROFILES,
  MOCK_TARGETS,
  MOCK_WASTE_RECORDS,
  MOCK_WATER_INCIDENTS,
} from "../mocks/sustainability.mock";

let passed = 0;
let failed = 0;

function assert(condition: boolean, message: string) {
  if (condition) {
    passed++;
    console.log(`  ✓ PASS: ${message}`);
  } else {
    failed++;
    console.error(`  ✗ FAIL: ${message}`);
  }
}

async function runSustainabilityTests() {
  console.log("\n==========================================================================");
  console.log("CampusOS Step 67 — Enterprise Campus Sustainability & Carbon Intelligence Suite");
  console.log("==========================================================================\n");

  // -------------------------------------------------------------------------
  // 1. Sustainability Profiles & Target Roadmaps
  // -------------------------------------------------------------------------
  console.log("--- 1. Master Sustainability Profiles & Target Roadmaps ---");
  const profiles = await sustainabilityService.getProfiles();
  assert(profiles.length >= 1, `Loaded ${profiles.length} master sustainability profile(s)`);

  const primaryProfile = profiles[0];
  assert(primaryProfile.target_net_zero_year === 2040, "Target net-zero year is set to 2040");
  assert(primaryProfile.baseline_year === 2022, "Institutional baseline reference year is 2022");
  assert(Boolean(primaryProfile.coordinator_email), `Coordinator email present: ${primaryProfile.coordinator_email}`);

  // Test profile creation
  const newProfile = await sustainabilityService.createProfile({
    name: "Campus Green Mission 2035",
    code: "SUS-MISSION-2035",
    coordinator_name: "Dr. K. Swaminathan",
    coordinator_email: "greenswaminathan@apextech.edu",
    target_net_zero_year: 2035,
  });
  assert(newProfile.id.startsWith("sp-"), "New profile successfully generated with unique ID");
  assert(newProfile.target_net_zero_year === 2035, "New profile target year 2035 verified");

  // Test target milestones
  const targets = await sustainabilityService.getTargets();
  assert(targets.length >= 4, `Loaded ${targets.length} reduction targets`);

  const elecTarget = targets.find((t) => t.category === "ENERGY_REDUCTION");
  assert(Boolean(elecTarget), "Grid energy reduction target present");
  assert(elecTarget?.reduction_pct_target === 30.0, "Energy reduction target is 30.0%");
  assert(elecTarget?.reduction_pct_achieved === 20.0, "Achieved progress is 20.0%");

  // Test target creation with progress calculation
  const newTarget = await sustainabilityService.createTarget({
    category: "RENEWABLE_SHARE",
    target_code: "TGT-EXP-SOLAR",
    title: "Phase-3 Solar Rooftop Expansion",
    baseline_year: 2022,
    baseline_value: 1000000,
    target_year: 2028,
    target_value: 600000,
    current_value: 800000, // (1,000,000 - 800,000)/1,000,000 = 20%
    unit: "kWh",
    reduction_pct_target: 40.0,
    responsible_team: "Solar Team",
  });
  assert(newTarget.reduction_pct_achieved === 20.0, "Calculated reduction percentage achieved is 20.0%");
  assert(newTarget.status === "ON_TRACK", "Target default status is ON_TRACK");

  // -------------------------------------------------------------------------
  // 2. Emission Factors Registry (Scope 1, 2, 3)
  // -------------------------------------------------------------------------
  console.log("\n--- 2. Emission Factors Registry & Standards ---");
  const factors = await sustainabilityService.getEmissionFactors();
  assert(factors.length >= 4, `Loaded ${factors.length} verified emission factors`);

  const ceaGrid = factors.find((f) => f.factor_code.includes("CEA"));
  assert(Boolean(ceaGrid), "CEA India grid emission factor registered");
  assert(ceaGrid?.factor_value === 0.716, "CEA grid factor is 0.716 kgCO2e/kWh");
  assert(ceaGrid?.scope === "SCOPE_2", "Grid electricity classified as SCOPE_2");

  const dieselFactor = factors.find((f) => f.category === "DIESEL");
  assert(Boolean(dieselFactor), "Diesel combustion factor registered");
  assert(dieselFactor?.factor_value === 2.68, "Diesel factor is 2.68 kgCO2e/L");
  assert(dieselFactor?.scope === "SCOPE_1", "Diesel combustion classified as SCOPE_1");

  // -------------------------------------------------------------------------
  // 3. Resource Measurements & Automated Anomaly Detection Engine
  // -------------------------------------------------------------------------
  console.log("\n--- 3. Resource Measurements & Automated Anomaly Detection Engine ---");
  const measurements = await sustainabilityService.getMeasurements();
  assert(measurements.length >= 4, `Loaded ${measurements.length} resource measurements`);

  // Test normal reading (within threshold)
  const normalMeas = await sustainabilityService.recordMeasurement({
    campus_id: MOCK_CAMPUS_ID,
    building_name: "Mechanical Engineering Block",
    meter_code: "MTR-MECH-01",
    resource_type: "ELECTRICITY_GRID",
    period_start: "2024-06-28T00:00:00Z",
    period_end: "2024-06-28T23:59:59Z",
    reading_value: 3200,
    unit: "kWh",
    source_type: "IOT_SENSOR",
    baseline_expected_value: 3000, // 6.7% variance -> normal
  });
  assert(normalMeas.is_anomaly === false, "Normal reading variance (6.7%) not flagged as anomaly");
  assert(normalMeas.anomaly_severity === "NORMAL", "Severity is NORMAL");

  // Test elevated reading (>30% variance -> WARNING)
  const warningMeas = await sustainabilityService.recordMeasurement({
    campus_id: MOCK_CAMPUS_ID,
    building_name: "Library Server Lab",
    meter_code: "MTR-SRV-01",
    resource_type: "ELECTRICITY_GRID",
    period_start: "2024-06-28T00:00:00Z",
    period_end: "2024-06-28T23:59:59Z",
    reading_value: 4100,
    unit: "kWh",
    source_type: "IOT_SENSOR",
    baseline_expected_value: 3000, // 36.7% variance -> WARNING
  });
  assert(warningMeas.is_anomaly === true, "Reading with 36.7% spike flagged as anomaly");
  assert(warningMeas.anomaly_severity === "WARNING", "Anomaly severity correctly tagged as WARNING");

  // Test severe spike reading (>50% variance -> CRITICAL)
  const criticalMeas = await sustainabilityService.recordMeasurement({
    campus_id: MOCK_CAMPUS_ID,
    building_name: "Chiller Plant Central",
    meter_code: "MTR-CHILL-01",
    resource_type: "ELECTRICITY_GRID",
    period_start: "2024-06-28T00:00:00Z",
    period_end: "2024-06-28T23:59:59Z",
    reading_value: 5200,
    unit: "kWh",
    source_type: "IOT_SENSOR",
    baseline_expected_value: 3000, // 73.3% variance -> CRITICAL
  });
  assert(criticalMeas.is_anomaly === true, "Reading with 73.3% spike flagged as anomaly");
  assert(criticalMeas.anomaly_severity === "CRITICAL", "Anomaly severity correctly tagged as CRITICAL");

  // -------------------------------------------------------------------------
  // 4. Water Resources & Leak Remediation Workflow
  // -------------------------------------------------------------------------
  console.log("\n--- 4. Water Resources & Leak Remediation Workflow ---");
  const waterIncidents = await sustainabilityService.getWaterIncidents();
  assert(waterIncidents.length >= 2, `Loaded ${waterIncidents.length} water incidents`);

  // Report new leak incident
  const newIncident = await sustainabilityService.reportWaterIncident({
    campus_id: MOCK_CAMPUS_ID,
    incident_code: "INC-TEST-01",
    incident_type: "LEAK_PIPE",
    location: "Auditorium Chilled Water Loop",
    estimated_loss_litres: 3500,
    severity: "HIGH",
    remediation_notes: "Isolation valve closed, dispatching plumbing emergency crew.",
  });
  assert(newIncident.id.startsWith("wi-"), "Water incident created with unique ID");
  assert(newIncident.status === "DETECTED", "Initial incident status is DETECTED");
  assert(newIncident.estimated_loss_litres === 3500, "Estimated loss recorded as 3,500 Litres");

  // -------------------------------------------------------------------------
  // 5. Waste Records & Regulated Hazardous Manifests
  // -------------------------------------------------------------------------
  console.log("\n--- 5. Waste Records & Hazardous TSDF Manifests ---");
  const wasteRecords = await sustainabilityService.getWasteRecords();
  assert(wasteRecords.length >= 3, `Loaded ${wasteRecords.length} waste records`);

  const hazWaste = wasteRecords.find((w) => w.is_hazardous);
  assert(Boolean(hazWaste), "Regulated hazardous waste record found");
  assert(Boolean(hazWaste?.manifest_number), `TSDF manifest number present: ${hazWaste?.manifest_number}`);
  assert(Boolean(hazWaste?.certificate_ref), `Disposal certificate present: ${hazWaste?.certificate_ref}`);

  // Log non-hazardous compost waste
  const compostRecord = await sustainabilityService.recordWaste({
    campus_id: MOCK_CAMPUS_ID,
    waste_code: "WST-COMP-NEW",
    waste_category: "ORGANIC_COMPOST",
    is_hazardous: false,
    quantity: 1800,
    unit: "kg",
    collection_date: "2024-06-29",
    disposal_method: "COMPOSTING",
    partner_name: "Campus Organic Agro Farm",
  });
  assert(compostRecord.quantity === 1800, "Compost waste quantity 1,800 kg verified");
  assert(compostRecord.is_hazardous === false, "Hazardous flag is false for compost");

  // -------------------------------------------------------------------------
  // 6. GHG Protocol Carbon Emissions Engine
  // -------------------------------------------------------------------------
  console.log("\n--- 6. Carbon Emissions Engine (Scope 1, 2, 3) ---");
  // Calculate Scope 2 grid emissions: 50,000 kWh * 0.716 kgCO2e/kWh = 35,800 kg = 35.8 MT
  const scope2Calc = await sustainabilityService.calculateEmissions({
    campus_id: MOCK_CAMPUS_ID,
    reporting_period: "2024-Q2",
    scope: "SCOPE_2",
    activity_category: "ELECTRICITY_GRID",
    activity_quantity: 50000,
    activity_unit: "kWh",
  });
  assert(scope2Calc.emissions_kg_co2e === 35800, "Scope 2 emissions calculated as 35,800 kgCO2e");
  assert(scope2Calc.emissions_mt_co2e === 35.8, "Scope 2 emissions converted to 35.80 MT CO2e");

  // Calculate Scope 1 diesel emissions: 2,000 Litres * 2.68 = 5,360 kg = 5.36 MT
  const scope1Calc = await sustainabilityService.calculateEmissions({
    campus_id: MOCK_CAMPUS_ID,
    reporting_period: "2024-Q2",
    scope: "SCOPE_1",
    activity_category: "DIESEL",
    activity_quantity: 2000,
    activity_unit: "Litre",
  });
  assert(scope1Calc.emissions_kg_co2e === 5360, "Scope 1 emissions calculated as 5,360 kgCO2e");
  assert(scope1Calc.emissions_mt_co2e === 5.36, "Scope 1 emissions converted to 5.36 MT CO2e");

  // Fetch summary
  const carbonSummary = await sustainabilityService.getCarbonSummary(MOCK_CAMPUS_ID, "2024-Q1");
  assert(carbonSummary.total_scope_1_mt > 0, "Summary contains Scope 1 totals");
  assert(carbonSummary.total_scope_2_mt > 0, "Summary contains Scope 2 totals");
  assert(carbonSummary.net_emissions_mt > 0, "Net carbon emissions calculated after solar offset");

  // -------------------------------------------------------------------------
  // 7. Green Sustainability Initiatives Portfolio
  // -------------------------------------------------------------------------
  console.log("\n--- 7. Sustainability Initiatives Portfolio ---");
  const initiatives = await sustainabilityService.getInitiatives();
  assert(initiatives.length >= 3, `Loaded ${initiatives.length} green capital projects`);

  const solarProject = initiatives.find((i) => i.category === "SOLAR_ROOFTOP");
  assert(Boolean(solarProject), "Rooftop solar initiative found");
  assert(solarProject?.annual_co2_savings_mt === 580.0, "Annual avoided emissions is 580.0 MT");

  // Propose new initiative
  const newInit = await sustainabilityService.createInitiative({
    campus_id: MOCK_CAMPUS_ID,
    initiative_code: "INIT-LED-RETRO",
    title: "100% Campus Smart LED Fixture Retrofit",
    description: "Replace all fluorescent tube lights across 5 academic blocks with daylight-sensing LEDs.",
    category: "LED_RETROFIT",
    status: "PROPOSED",
    budget_allocated: 1500000,
    budget_spent: 0,
    annual_co2_savings_mt: 85.0,
    annual_energy_savings_kwh: 118000,
    annual_water_savings_kl: 0,
    start_date: "2024-07-01",
    lead_department: "Electrical Engineering Cell",
  });
  assert(newInit.initiative_code === "INIT-LED-RETRO", "New initiative created with valid code");
  assert(newInit.annual_co2_savings_mt === 85.0, "Annual CO2 savings recorded as 85.0 MT");

  // -------------------------------------------------------------------------
  // 8. Environmental Compliance Requirements & CAPA
  // -------------------------------------------------------------------------
  console.log("\n--- 8. Statutory Environmental Compliance & CAPA ---");
  const reqs = await sustainabilityService.getComplianceRequirements();
  assert(reqs.length >= 3, `Loaded ${reqs.length} environmental compliance permits`);

  const ctoPermit = reqs.find((r) => r.compliance_code.includes("CTO"));
  assert(Boolean(ctoPermit), "Consent to Operate (CTO) statutory permit registered");
  assert(Boolean(ctoPermit?.regulatory_body.includes("TNPCB")), "Regulatory body is TNPCB");

  const actions = await sustainabilityService.getCorrectiveActions();
  assert(actions.length >= 1, `Loaded ${actions.length} corrective action items (CAPA)`);
  assert(actions[0].priority === "HIGH", "Action item has HIGH priority");

  // Register new permit
  const newPermit = await sustainabilityService.createComplianceRequirement({
    campus_id: MOCK_CAMPUS_ID,
    compliance_code: "COMP-AIR-NOC",
    regulation_title: "Air (Prevention and Control of Pollution) Act - DG Stack Emission NOC",
    regulatory_body: "Tamil Nadu Pollution Control Board",
    compliance_category: "AIR_EMISSIONS",
    frequency: "ANNUAL",
    next_renewal_date: "2025-05-31",
    status: "COMPLIANT",
    permit_number: "TNPCB/AIR/DG-9921",
  });
  assert(newPermit.compliance_code === "COMP-AIR-NOC", "New air consent permit registered successfully");

  // -------------------------------------------------------------------------
  // 9. IoT Smart Meters & Ingestion
  // -------------------------------------------------------------------------
  console.log("\n--- 9. IoT Smart Meters & Ingestion Stream ---");
  const meters = await sustainabilityService.getIoTMeters();
  assert(meters.length >= 3, `Loaded ${meters.length} IoT meter streams`);

  const onlineMeter = meters.find((m) => m.status === "ONLINE");
  assert(Boolean(onlineMeter), "Online IoT smart meter found");

  // Ingest live telemetry event
  const event = await sustainabilityService.ingestTelemetry({
    device_id: "MTR-SMART-SUB-01",
    event_timestamp: new Date().toISOString(),
    metric_name: "active_power_kwh",
    metric_value: 418.5,
    unit: "kWh",
  });
  assert(event.ingestion_status === "PROCESSED", "Telemetry event status is PROCESSED");
  assert(Boolean(event.dedup_hash), "Cryptographic deduplication hash generated");

  // -------------------------------------------------------------------------
  // 10. Utility Imports & Executive ESG Scorecard
  // -------------------------------------------------------------------------
  console.log("\n--- 10. Utility Invoices & ESG Scorecard Overview ---");
  const batches = await sustainabilityService.getImportBatches();
  assert(batches.length >= 1, `Loaded ${batches.length} import batch records`);
  assert(batches[0].status === "COMPLETED", "Import batch completed successfully");

  const overview = await sustainabilityService.getDashboardOverview();
  assert(overview.esg_composite_score > 80, `ESG Composite Score is high: ${overview.esg_composite_score}/100`);
  assert(overview.statutory_compliance_rate_pct === 100.0, "Statutory compliance rate is 100.0%");
  assert(overview.renewable_share_pct > 30, `Renewable solar share is ${overview.renewable_share_pct}%`);

  // -------------------------------------------------------------------------
  // Summary
  // -------------------------------------------------------------------------
  console.log("\n==========================================================================");
  console.log(`TEST RESULTS: ${passed} PASSED, ${failed} FAILED`);
  console.log("==========================================================================\n");

  if (failed > 0) {
    process.exit(1);
  }
}

runSustainabilityTests().catch((err) => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
