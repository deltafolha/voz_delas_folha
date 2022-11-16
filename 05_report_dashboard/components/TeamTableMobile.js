export default function TeamTableMobile (props) {
    return (
        <section className="min-h-screen min-w-full bg-gray-100 flex">
            <div className="my-14 mx-5 w-full">
            {props.team.map((teamMember, index) => 
                <div key={index} className="bg-white my-2 p-4 space-y-2 rounded-lg shadow">
                    <div className="flex items-center space-x-2 text-xs">
                        <div href="#" className="text-blue-500 text-sm font-bold hover:underline cursor-pointer">{teamMember.name}</div>
                    </div>
                    <div className="text-xs">{teamMember.channel} | {teamMember.role}</div>
                    <div className="text-xs">{teamMember.email}</div>
                    <div><button onClick={() => props.deleteTeamMember(teamMember)}><i className="fa fa-trash cursor-pointer" aria-hidden="true"></i></button></div>
                </div>
            )}
            </div>
        </section>
    )
}