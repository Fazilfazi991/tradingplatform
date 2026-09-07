import type { Metadata } from "next";
import { PublicDoc } from "@/components/public-doc";
export const metadata: Metadata = { title: "Contact", robots: { index: false, follow: false } };
export default function Contact(){return <PublicDoc draft title="Contact" summary="The public support and privacy contact channel is pending owner approval."><h2>Pre-release status</h2><p>No public support inbox or operating entity has been approved for publication. A monitored contact channel, response expectation, privacy contact, and security-reporting route must be added before production.</p></PublicDoc>}
