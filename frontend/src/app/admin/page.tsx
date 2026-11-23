import { redirect } from "next/navigation";

/** Direct entry point for the existing administrator portal. */
export default function AdminEntryPage() {
  redirect("/login?role=ADMIN&portal=admin");
}
