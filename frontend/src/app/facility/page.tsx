import { redirect } from "next/navigation";

export default function FacilityPortalEntryPage() {
  redirect("/login?role=facility");
}
