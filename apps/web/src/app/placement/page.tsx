import { redirect } from "next/navigation";

export default function PlacementPortalEntryPage() {
  redirect("/login?role=placement");
}
