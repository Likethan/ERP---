import { redirect } from "next/navigation";

export default function WardenPortalEntryPage() {
  redirect("/login?role=warden");
}
