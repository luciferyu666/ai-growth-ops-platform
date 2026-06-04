import { NextResponse, type NextRequest } from "next/server";

import { getAuth0Client, isAuth0Enabled } from "@/lib/auth0";

export async function proxy(request: NextRequest) {
  if (!isAuth0Enabled()) {
    return NextResponse.next();
  }

  return getAuth0Client().middleware(request);
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)",
  ],
};
