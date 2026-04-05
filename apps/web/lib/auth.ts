"use client";

import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
  CognitoUserAttribute,
  CognitoUserSession,
} from "amazon-cognito-identity-js";

const POOL_DATA = {
  UserPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID ?? "",
  ClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID ?? "",
};

let pool: CognitoUserPool | null = null;

function getUserPool(): CognitoUserPool {
  if (!pool) {
    pool = new CognitoUserPool(POOL_DATA);
  }
  return pool;
}

/** Get the current session (JWT tokens) if the user is signed in. */
export function getSession(): Promise<CognitoUserSession | null> {
  return new Promise((resolve) => {
    const user = getUserPool().getCurrentUser();
    if (!user) return resolve(null);
    user.getSession(
      (err: Error | null, session: CognitoUserSession | null) => {
        if (err || !session?.isValid()) return resolve(null);
        resolve(session);
      },
    );
  });
}

/** Get the current ID token (JWT) string, or null if not authenticated. */
export async function getIdToken(): Promise<string | null> {
  const session = await getSession();
  return session?.getIdToken().getJwtToken() ?? null;
}

/** Sign in with email and password. Returns session on success. */
export function signIn(
  email: string,
  password: string,
): Promise<CognitoUserSession> {
  return new Promise((resolve, reject) => {
    const user = new CognitoUser({
      Username: email,
      Pool: getUserPool(),
    });
    const authDetails = new AuthenticationDetails({
      Username: email,
      Password: password,
    });
    user.authenticateUser(authDetails, {
      onSuccess: (session) => resolve(session),
      onFailure: (err) => reject(err),
    });
  });
}

/** Register a new user with email and password. */
export function signUp(
  email: string,
  password: string,
  displayName: string,
): Promise<CognitoUser | undefined> {
  return new Promise((resolve, reject) => {
    const attributes = [
      new CognitoUserAttribute({ Name: "email", Value: email }),
      new CognitoUserAttribute({ Name: "name", Value: displayName }),
    ];
    getUserPool().signUp(email, password, attributes, [], (err, result) => {
      if (err) return reject(err);
      resolve(result?.user);
    });
  });
}

/** Confirm signup with the emailed verification code. */
export function confirmSignUp(
  email: string,
  code: string,
): Promise<"SUCCESS"> {
  return new Promise((resolve, reject) => {
    const user = new CognitoUser({
      Username: email,
      Pool: getUserPool(),
    });
    user.confirmRegistration(code, true, (err, result) => {
      if (err) return reject(err);
      resolve(result);
    });
  });
}

/** Sign the user out (clear local session). */
export function signOut(): void {
  const user = getUserPool().getCurrentUser();
  user?.signOut();
}
