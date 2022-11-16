import ChannelFilter from "./ChannelFilter";

export default function TeamTableDesktop (props) {
    return (
        <section className="min-h-screen py-20 bg-gray-100 flex flex-wrap">
            <ChannelFilter/>
            <div className="w-full w-11/12 mx-auto overflow-auto rounded-lg shadow hidden md:block">
                <table className="w-full table-auto">
                    <thead className="bg-gray-50 border-b-2 border-gray-200">
                        <tr>
                            <th className="p-3 text-xs font-semibold tracking-wide text-left">NOME</th>
                            <th className="p-3 text-xs font-semibold tracking-wide text-left">EDITORIA</th>
                            <th className="p-3 text-xs font-semibold tracking-wide text-left">CARGO</th>
                            <th className="p-3 text-xs font-semibold tracking-wide text-left">E-MAIL</th>
                            <th className="p-3 text-xs font-semibold tracking-wide text-left"></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y">
                    {props.team.map((teamMember, index) => 
                        <tr className={ index % 2 == 0 ? "bg-white" : "bg-gray-50"} key={index}>
                            <td className="p-3 text-xs text-gray-700">{teamMember.name}</td>
                            <td className="p-3 text-xs text-gray-700">{teamMember.channel}</td>
                            <td className="p-3 text-xs text-gray-700">{teamMember.role}</td>
                            <td className="p-3 text-xs text-gray-700">{teamMember.email}</td>
                            <td className="p-3 text-xs text-gray-700 text-right"><button onClick={() => props.deleteTeamMember(teamMember)}><i className="fa fa-trash cursor-pointer text-sm" aria-hidden="true"></i></button></td>
                        </tr>
                    )}
                    </tbody>
                </table>
            </div>
        </section>
    )
}