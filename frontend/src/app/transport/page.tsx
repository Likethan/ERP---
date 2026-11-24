import { redirect } from "next/navigation";

export default function TransportPortalEntryPage() {
  redirect("/login?role=transport");
}
