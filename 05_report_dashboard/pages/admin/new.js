import axios from "axios";
import { useRouter } from "next/router";
import { isMobile } from 'react-device-detect';
import { useSession } from "next-auth/react";
import Navbar from "../../components/Navbar";

export default function NewTeamMember () {
    const channels = process.env.NEXT_PUBLIC_CHANNELS.split(",")
    const roles = process.env.NEXT_PUBLIC_ROLES.split(",")
    const { status, data } = useSession();
    const router = useRouter();

    const insertTeamMember = async (e) => {
        e.preventDefault();
        const body = {
            name: e.target.elements.name.value,
            channel: e.target.elements.channel.value,
            role: e.target.elements.role.value,
            email: e.target.elements.email.value
        }
        const insertTeamMemberResult = await axios.post("/api/team/new", body);
        if (insertTeamMemberResult.status == 200) {
            router.push("/admin")
        }
    }

    if (status == "unauthenticated") { router.push("/auth/signin") } 
    if (status == "authenticated") {
        return (
            <>
                <Navbar isMobile={isMobile} user={data.user.name}></Navbar>
                <section className="flex min-h-screen bg-gray-100">
                    <div className="container mx-auto my-auto p-10 sm:w-5/6 md:bg-white lg:w-1/2 bg-gray-100">
                        <form onSubmit={insertTeamMember} method="post" className="w-full mx-auto">
                            <div className="flex flex-wrap -mx-3">
                                <div className="w-full px-3 mb-2">
                                    <label className="block uppercase tracking-wide text-gray-700 text-xs font-bold mb-2">
                                        NOME
                                    </label>
                                    <input id="name" name="name" className="appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 mb-3 leading-tight focus:outline-none focus:bg-white" type="text" placeholder=""></input>
                                </div>
                            </div>
                            <div className="flex flex-wrap -mx-3 mb-6">
                                <div className="w-full md:w-1/2 px-3 mb-6 lg:mb-0">
                                    <label className="block uppercase tracking-wide text-gray-700 text-xs font-bold mb-2">
                                        EDITORIA
                                    </label>
                                    <div className="relative">
                                        <select id="channel" name="channel" className="block appearance-none w-full bg-gray-200 border border-gray-200 text-gray-700 py-3 px-4 pr-8 rounded leading-tight focus:outline-none focus:bg-white focus:border-gray-500">
                                            {channels.map((channel, index) => <option key={index}>{channel}</option>)}
                                        </select>
                                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                                        <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                                        </div>
                                    </div>
                                </div>
                                <div className="w-full md:w-1/2 px-3 md:mb-0">
                                    <label className="block uppercase tracking-wide text-gray-700 text-xs font-bold mb-2">
                                        CARGO
                                    </label>
                                    <div className="relative">
                                        <select id="role" name="role" className="block appearance-none w-full bg-gray-200 border border-gray-200 text-gray-700 py-3 px-4 pr-8 rounded leading-tight focus:outline-none focus:bg-white focus:border-gray-500">
                                            {roles.map((role, index) => <option key={index}>{role}</option>)}
                                        </select>
                                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                                        <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="flex flex-wrap -mx-3">
                                <div className="w-full px-3 mb-2">
                                    <label className="block uppercase tracking-wide text-gray-700 text-xs font-bold mb-2">
                                        E-MAIL
                                    </label>
                                    <input id="email" name="email" className="appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 mb-3 leading-tight focus:outline-none focus:bg-white" type="text" placeholder=""></input>
                                </div>
                            </div>
                            <button type="submit" className="bg-blue-500 text-sm hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                                ENVIAR
                            </button>
                        </form>
                    </div>
                </section>
            </>
        )
    }
}