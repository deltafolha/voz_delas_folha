import Link from "next/link";
import Image from "next/image";
import logo from "../public/logo.svg";
import { signOut } from "next-auth/react";

export default function Navbar (props) {
    return (
        <nav className="fixed w-full justify-between bg-gradient-to-r from-cyan-500 to-blue-500 py-2 z-50">
            <div className="flex justify-between w-11/12 mx-auto">
                <div className={`my-auto`}>
                    <Link href="/"><a><Image src={logo} alt="Identidade visual da Folha de S.Paulo." className="fill-current"></Image></a></Link>
                </div>
                { props.user ? (
                    <div>
                        {props.isMobile == false ? (
                        <>
                            <div className="inline-block">
                                <Link href="/admin"><h2 className="text-xs px-4 py-2 leading-none border rounded text-white border-white mr-2 uppercase cursor-pointer">Olá, {props.user.replace("@grupofolha.com.br", "")} 👋</h2></Link>
                            </div>
                        </>
                        ) : (null)}
                        <Link href="/admin/new"><a className="inline-block font-bold text-xs px-4 py-2 leading-none border rounded text-white border-white hover:border-transparent hover:text-teal-500 hover:bg-white mt-0 mr-2">+</a></Link>
                        <button className="inline-block font-bold text-xs px-4 py-2 leading-none border rounded text-white border-white hover:border-transparent hover:text-teal-500 hover:bg-white mt-0" onClick={() => signOut()}>Sair</button>
                    </div>
                ) : (
                    <div></div>
                )}
            </div>
        </nav>
    )
}