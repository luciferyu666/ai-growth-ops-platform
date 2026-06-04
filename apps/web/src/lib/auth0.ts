import { Auth0Client } from "@auth0/nextjs-auth0/server";

let auth0Client: Auth0Client | null = null;

export function isAuth0Enabled() {
  return (
    process.env.AUTH_PROVIDER === "auth0" ||
    process.env.NEXT_PUBLIC_AUTH_PROVIDER === "auth0"
  );
}

export function getAuth0Client() {
  if (!auth0Client) {
    auth0Client = new Auth0Client({
      authorizationParameters: {
        audience: process.env.AUTH0_AUDIENCE,
        scope: process.env.AUTH0_SCOPE ?? "openid profile email",
      },
    });
  }
  return auth0Client;
}
