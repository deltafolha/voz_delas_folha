import axios from "axios";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { isMobile } from 'react-device-detect';
import { useSession } from "next-auth/react";
import Navbar from "../../components/Navbar";
import TeamTable from "../../components/TeamTable";
import Loading from "../../components/Loading";

export default function Admin() {
  	const { status, data } = useSession();
  	const [ team, setTeam ] = useState([]);
  	const router = useRouter();

	useEffect(() => {
		if (status == "authenticated") {
			async function getTeamMembers() {
				const teamFetchResponse = await axios.get("/api/team");
				setTeam(teamFetchResponse.data.team);
			}
			getTeamMembers();
		}
	}, [status])

	if (status == "unauthenticated") { router.push("/auth/signin") }  
	if (status == "authenticated") {
		return (
			<>
				<Navbar isMobile={isMobile} user={data.user.name}/>
				{team.length > 0 ? (<TeamTable team={team} setTeam={setTeam}/>) : (<Loading/>)}
			</>
		)
	}
}