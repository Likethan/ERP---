import { redirect } from "next/navigation";

export default function AccountsPortalEntryPage() {
  redirect("/login?role=accounts");
}
