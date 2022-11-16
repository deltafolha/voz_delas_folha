import axios from "axios";
import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";

export default function ChannelFilter(props) {
    const { status, data } = useSession();
    const [ channels, setChannels ] = useState(["🔁 CARREGANDO EDITORIAS"]);

	useEffect(() => {
		if (status == "authenticated") {
			async function getChannels() {
				const channelFetchResponse = await axios.get("/api/team/channels");
				setChannels(["TODAS"].concat(channelFetchResponse.data.channels));
			}
			getChannels();
		}
	}, [status])
    
    return (
        <div className="w-full w-11/12 mx-auto mb-5">
            <div className="w-full w-3/12 sticky">
                <select id="channel" name="channel" className="block appearance-none w-full bg-gray-50 border border-gray-200 text-gray-700 text-xs py-3 px-4 pr-8 rounded leading-tight focus:outline-none focus:bg-white focus:border-gray-300">
                    {channels.map((channel, index) => <option key={index}>{channel}</option>)}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                    <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                </div>
            </div>
        </div>
    )
}