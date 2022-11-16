import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

export const authOptions = {
    session: {
        strategy: "jwt"
    },
    providers: [
        CredentialsProvider({
            type: "credentials",
            credentials: {},
            authorize(credentials, request) {
                const {username, password} = credentials;
                // PERFORM LOGIN LOGIC
                if (username !== process.env.ADMIN_USERNAME || password !== process.env.ADMIN_PASSWORD) {
                    return null;
                }
                return { 
                    name: process.env.ADMIN_USERNAME
                }
            },  
        }),
    ],
    pages: {
        signIn: "/auth/signin"
    }
}

export default NextAuth(authOptions);