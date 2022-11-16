import axios from "axios";
import { isMobile } from 'react-device-detect';
import TeamTableMobile from "../components/TeamTableMobile";
import TeamTableDesktop from "../components/TeamTableDesktop";

export default function TeamTable (props) {
    const deleteTeamMember = async teamMember => {
        const deleteTeamMemberResult = await axios.delete(`/api/team/delete/${teamMember.email}`);
        if (deleteTeamMemberResult.data.result == 1) {
          props.setTeam(props.team.filter(t => t.email !== teamMember.email));
        }
    }
    return (
        <>
            {isMobile ? (
                <TeamTableMobile team={props.team} setTeam={props.setTeam} deleteTeamMember={deleteTeamMember}></TeamTableMobile>
                ) : (
                <TeamTableDesktop team={props.team} setTeam={props.setTeam} deleteTeamMember={deleteTeamMember}></TeamTableDesktop>
                )}
        </>
    )
}