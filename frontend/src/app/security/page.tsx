import { redirect } from "next/navigation";

export default function SecurityPortalEntryPage() {
  redirect("/login?role=security");
}
