import Head from "next/head";
import '../styles/globals.css';
import { SessionProvider } from "next-auth/react";

export default function MyApp({ Component, pageProps: { session, ...pageProps } }) {
  return (
    <>
      <Head><title>Voz Delas</title></Head>
      <SessionProvider session={session}>
        <Component {...pageProps} />
      </SessionProvider>
    </>
  )
}