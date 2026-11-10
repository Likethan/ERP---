import { redirect } from "next/navigation";

export default function VicePrincipalPortalEntryPage() {
  redirect("/login?role=vice_principal");
}
