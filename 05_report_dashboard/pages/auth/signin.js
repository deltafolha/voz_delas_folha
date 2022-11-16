import { useState } from "react";
import { useRouter } from "next/router";
import { signIn } from "next-auth/react";

export default function SignIn () {
    const router = useRouter();
    const [userInfo, setUserInfo] = useState({ username: '', password: '' })
    const handleSignIn = async (e) => {
        // VALIDATE USER INFO
        e.preventDefault();
        const result = await signIn("credentials", {
            username: userInfo.username,
            password: userInfo.password,
            redirect: false
        })
        if (result.status == 200 && result.ok == true && result.error == null) {
            router.push("/admin");
        }
    }

    return (
        <section className="flex min-h-screen bg-gray-100">
            <div className="w-full max-w-xs mx-auto my-auto">
                <form onSubmit={handleSignIn} className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
                    <div className="mb-4">
                        <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="username">
                            Usuário/a
                        </label>
                        <input className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline" id="username" type="text" placeholder="" value={userInfo.username} onChange={({target}) => setUserInfo({...userInfo, username: target.value})}></input>
                    </div>
                    <div className="mb-6">
                        <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">
                            Senha
                        </label>
                        <input className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline" id="password" type="password" placeholder="" value={userInfo.password} onChange={({target}) => setUserInfo({...userInfo, password: target.value})}></input>
                    </div>
                    <div className="flex items-center justify-between">
                        <button type="submit" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
                            Entrar
                        </button>
                    </div>
                </form>
            </div>
        </section>
    )
}