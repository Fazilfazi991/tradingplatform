import { NextRequest, NextResponse } from "next/server";
import { validBasicAuthorization } from "@/lib/internal-auth";
import { isInternalPath } from "@/lib/route-policy";

function authorized(request: NextRequest): boolean {
  return validBasicAuthorization(
    request.headers.get("authorization"),
    process.env.VERIFIED_EDGE_INTERNAL_USERNAME,
    process.env.VERIFIED_EDGE_INTERNAL_PASSWORD,
  );
}

export function proxy(request: NextRequest) {
  if (!isInternalPath(request.nextUrl.pathname)) return NextResponse.next();
  if (!authorized(request)) {
    return new NextResponse("Internal operator access required.", {
      status: 401,
      headers: {
        "Cache-Control": "no-store",
        "Content-Type": "text/plain; charset=utf-8",
        "WWW-Authenticate": 'Basic realm="Verified Edge internal", charset="UTF-8"',
        "X-Robots-Tag": "noindex, nofollow, noarchive",
      },
    });
  }

  const response = NextResponse.next();
  response.headers.set("Cache-Control", "private, no-store");
  response.headers.set("X-Robots-Tag", "noindex, nofollow, noarchive");
  return response;
}

export const config = {
  matcher: [
    "/research/:path*",
    "/research-desk/:path*",
    "/data-health/:path*",
    "/settings/:path*",
    "/api/research-desk/:path*",
  ],
};
