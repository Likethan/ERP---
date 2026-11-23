import { redirect } from "next/navigation";

export default function HodPortalEntryPage() {
  redirect("/login?role=hod");
}
