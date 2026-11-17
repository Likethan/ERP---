import { redirect } from "next/navigation";

export default function StaffPortalEntryPage() {
  redirect("/login?role=staff");
}
